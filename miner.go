package main

import (
	"crypto/rand"
	"encoding/binary"
	"encoding/hex"
	"flag"
	"fmt"
	"math/bits"
	"os"
	"runtime"
	"strings"
	"sync/atomic"
	"time"

	"github.com/decred/dcrd/dcrec/secp256k1/v4"
	"golang.org/x/crypto/sha3"
)

var totalAttempts uint64

// xoshiro256** — fast non-crypto PRNG, seeded per goroutine from crypto/rand
type xoshiro256 struct{ s [4]uint64 }

func newRand() *xoshiro256 {
	var seed [32]byte
	rand.Read(seed[:])
	return &xoshiro256{s: [4]uint64{
		binary.LittleEndian.Uint64(seed[0:8]),
		binary.LittleEndian.Uint64(seed[8:16]),
		binary.LittleEndian.Uint64(seed[16:24]),
		binary.LittleEndian.Uint64(seed[24:32]),
	}}
}

func (r *xoshiro256) next() uint64 {
	result := bits.RotateLeft64(r.s[1]*5, 7) * 9
	t := r.s[1] << 17
	r.s[2] ^= r.s[0]
	r.s[3] ^= r.s[1]
	r.s[1] ^= r.s[2]
	r.s[0] ^= r.s[3]
	r.s[2] ^= t
	r.s[3] = bits.RotateLeft64(r.s[3], 45)
	return result
}

func (r *xoshiro256) read(b []byte) {
	for i := 0; i+8 <= len(b); i += 8 {
		binary.LittleEndian.PutUint64(b[i:], r.next())
	}
}

type result struct {
	address string
	privKey string
	slot    int
}

// perWorkerRate is the per-goroutine throughput cap in addr/s. 0 = unlimited.
func worker(results chan<- result, perWorkerRate float64) {
	rng := newRand()
	privBytes := make([]byte, 32)
	pubBytes := make([]byte, 64)
	h := sha3.NewLegacyKeccak256()

	const batch = 2000
	var budget time.Duration
	if perWorkerRate > 0 {
		budget = time.Duration(float64(batch) / perWorkerRate * float64(time.Second))
	}

	for {
		t0 := time.Now()
		for i := 0; i < batch; i++ {
			rng.read(privBytes)

			var scalar secp256k1.ModNScalar
			if overflow := scalar.SetByteSlice(privBytes); overflow || scalar.IsZero() {
				continue
			}

			var pubKey secp256k1.JacobianPoint
			secp256k1.ScalarBaseMultNonConst(&scalar, &pubKey)
			pubKey.ToAffine()

			xb := pubKey.X.Bytes()
			yb := pubKey.Y.Bytes()
			copy(pubBytes[:32], xb[:])
			copy(pubBytes[32:], yb[:])

			h.Reset()
			h.Write(pubBytes)
			hash := h.Sum(nil)

			atomic.AddUint64(&totalAttempts, 1)

			// Check: bytes 12-13 must be 0xde, 0xad, then 5 decimal digits
			if hash[12] != 0xde || hash[13] != 0xad {
				continue
			}

			addr := hex.EncodeToString(hash[12:])
			// addr[4:9] = 5 digits after "dead"
			slotStr := addr[4:9]
			slot := 0
			valid := true
			for _, c := range slotStr {
				if c < '0' || c > '9' {
					valid = false
					break
				}
				slot = slot*10 + int(c-'0')
			}
			if valid && slot >= 1 && slot <= 10000 {
				pk := make([]byte, 32)
				copy(pk, privBytes)
				results <- result{
					address: "0x" + addr,
					privKey: "0x" + hex.EncodeToString(pk),
					slot:    slot,
				}
			}
		}

		// Throttle to the speed cap. Delete this block to run at full speed.
		if budget > 0 {
			if d := budget - time.Since(t0); d > 0 {
				time.Sleep(d)
			}
		}
	}
}

// maxRate is the total throughput cap in addr/s, split across all cores.
// Set to 0 (or just delete the throttle in worker) to run at full speed.
const maxRate = 75000

func main() {
	cores := flag.Int("cores", runtime.NumCPU(), "number of CPU cores")
	flag.Parse()

	perWorkerRate := 0.0
	if maxRate > 0 {
		perWorkerRate = float64(maxRate) / float64(*cores)
	}

	fmt.Printf("\n  xDead Go Miner (fast)\n")
	fmt.Printf("  Cores: %d / %d\n", *cores, runtime.NumCPU())
	fmt.Printf("  Target: 0xdead00001 — 0xdead10000\n")
	if maxRate > 0 {
		fmt.Printf("  Speed cap: %s addr/s total\n", formatNum(maxRate))
	}
	fmt.Printf("  Press Ctrl+C to stop\n\n")

	runtime.GOMAXPROCS(*cores)

	results := make(chan result, 64)

	for i := 0; i < *cores; i++ {
		go worker(results, perWorkerRate)
	}

	start := time.Now()
	found := 0

	go func() {
		ticker := time.NewTicker(time.Second)
		for range ticker.C {
			elapsed := time.Since(start).Seconds()
			total := atomic.LoadUint64(&totalAttempts)
			rate := uint64(float64(total) / elapsed)
			fmt.Printf("\r  ⛏  %s attempts | %s addr/s | Found: %d   ",
				formatNum(total), formatNum(rate), found)
		}
	}()

	for r := range results {
		found++
		elapsed := time.Since(start).Seconds()
		slotStr := fmt.Sprintf("%05d", r.slot)

		fmt.Printf("\n\n%s\n", strings.Repeat("=", 56))
		fmt.Printf("  FOUND #%d in %.1fs\n", found, elapsed)
		fmt.Printf("%s\n", strings.Repeat("=", 56))
		fmt.Printf("  Address:     %s\n", r.address)
		fmt.Printf("  Slot:        #%s\n", slotStr)
		fmt.Printf("  Private Key: %s\n", r.privKey)
		fmt.Printf("%s\n\n", strings.Repeat("=", 56))

		filename := fmt.Sprintf("found_slot_%s.txt", slotStr)
		content := fmt.Sprintf("Address:     %s\nSlot:        #%s\nPrivate Key: %s\n\nNext step: https://xdead.xyz/mint\n",
			r.address, slotStr, r.privKey)
		os.WriteFile(filename, []byte(content), 0600)
		fmt.Printf("  Saved to: %s\n  Continuing search...\n\n", filename)
	}
}

func formatNum(n uint64) string {
	s := fmt.Sprintf("%d", n)
	out := []byte{}
	for i, c := range s {
		if i > 0 && (len(s)-i)%3 == 0 {
			out = append(out, ',')
		}
		out = append(out, byte(c))
	}
	return string(out)
}
