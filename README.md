# xDead Wallet Finder

A script that generates random Ethereum wallets and searches for addresses matching the registry pattern **0xdead00001 — 0xdead10000**.

When found — it saves the private key and address to a `.txt` file. Bring that key to [xdead.xyz/mint](https://xdead.xyz/mint) to register your slot in the on-chain registry and receive **100 $DEAD**.

> **No install? Mine in your browser.** The easiest option is the built-in miner at **[xdead.xyz/mine](https://xdead.xyz/mine)** — it runs entirely on your machine, nothing to download. This CLI version is for people who want to run it locally.

---

## How it works

The script generates random private keys, derives the Ethereum address, and checks if it starts with `0xdead` followed by a 5-digit number between `00001` and `10000`. On average you'll find one every **3–4 million attempts**.

---

## Requirements

- Python 3.10+
- pip

---

## Install & Run

**1. Download the script**

```bash
git clone https://github.com/xDeadProject/xDead-finder.git
cd xDead-finder
```

Or just download `xdead_finder.py` directly.

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Run**

Single core:
```bash
python xdead_finder.py
```

Multi-core (faster — replace `4` with your CPU core count):
```bash
python xdead_finder.py --cores 4
```

---

## Fast version (Go)

For much higher throughput there's a native Go miner (`miner.go`). It is capped at **75,000 addr/s** out of the box — that's plenty to find a slot in ~1 minute, while staying light on your machine. (If you know what you're doing, the cap is a single constant — `maxRate` in `miner.go` — set it to `0` to run unthrottled.)

```bash
# needs Go 1.21+
go run miner.go --cores 4
```

Found wallets are saved to `found_slot_XXXXX.txt`, same as the Python version.

---

## Example output

```
==================================================
        xDead Wallet Finder v1.0
==================================================

  Attempts:  3,847,221  |  Speed:  6,400/s  |  Found: 0

==================================================
  FOUND! #1
  Address:     0xDEaD00042a3F1c8E4b2D9f7A...
  Slot:        #00042
  Private Key: 0xabc123...
  Attempts:    3,847,221
==================================================
  Saved to: found_slot_00042.txt
```

The private key is saved to `found_slot_00042.txt` in the same folder.

---

## How to use the found key

1. Go to **[xdead.xyz/mint](https://xdead.xyz/mint)**
2. Paste the private key from the `.txt` file
3. The key is processed **entirely in your browser** — never sent to any server
4. Follow the steps: tweet → connect your registration wallet → register the slot → receive 100 $DEAD

---

## Speed

This is pure Python, so it is the slow-but-simple option:

| Method | Rough speed |
|---|---|
| `python xdead_finder.py` | ~3,000–8,000/s per core |
| `python xdead_finder.py --cores 4` | scales with cores |

For more speed, use the **Go miner** (`go run miner.go`, see above) or the no-install **browser miner** at [xdead.xyz/mine](https://xdead.xyz/mine).

Check your CPU core count:
- Windows: Task Manager → Performance → CPU → Cores
- Mac/Linux: `nproc`

---

## Build your own version

Want to write your own finder? Here's the core logic:

```python
import os
import re
from eth_keys import keys as eth_keys

def check_address(address):
    lower = address.lower()
    if not lower.startswith("0xdead"):
        return None
    match = re.match(r"^(\d{5})", lower[6:])
    if not match:
        return None
    num = int(match.group(1))
    return num if 1 <= num <= 10000 else None

while True:
    pk = os.urandom(32)
    address = eth_keys.PrivateKey(pk).public_key.to_checksum_address()
    slot = check_address(address)
    if slot:
        print(f"Found slot #{slot:05d}: {address}")
        print(f"Private key: 0x{pk.hex()}")
        break
```

You can also ask an AI to build a faster version:

```
Write a Python script that generates random Ethereum private keys,
derives the address using eth_keys, and checks if the address starts
with "0xdead" followed by exactly 5 decimal digits forming a number
between 1 and 10000. Use multiprocessing for speed. When found, print
the address, slot number, and private key, then save to a file.
```

---

## Security

- The script runs **100% locally** on your machine
- No data is sent anywhere
- The private key of the found wallet never needs to touch the internet — xdead.xyz processes it client-side only
- The found wallet should hold nothing — it is only used as proof of work, separate from your registration wallet

---

## License

MIT
