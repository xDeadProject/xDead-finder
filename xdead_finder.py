"""
xDead Wallet Finder
===================
Generates random Ethereum wallets and searches for addresses matching
the pattern 0xdead00001 — 0xdead10000.

When found: saves private key + address to a .txt file.

Usage:
    python xdead_finder.py           # single core
    python xdead_finder.py --cores 4 # multi-core (faster)
"""

import os
import re
import time
import argparse
import multiprocessing
from eth_keys import keys as eth_keys


TARGET_MIN = 1
TARGET_MAX = 10000


def check_address(address: str) -> int | None:
    """Return slot number if address matches 0xdead00001-0xdead10000, else None."""
    lower = address.lower()
    if not lower.startswith("0xdead"):
        return None
    after = lower[6:]
    match = re.match(r"^(\d{5})", after)
    if not match:
        return None
    num = int(match.group(1))
    return num if TARGET_MIN <= num <= TARGET_MAX else None


def save_result(address: str, slot: int, private_key: str, attempts: int, elapsed: float):
    filename = f"found_slot_{slot:05d}.txt"
    with open(filename, "w") as f:
        f.write("=" * 50 + "\n")
        f.write("  xDead — WALLET FOUND\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Address:     {address}\n")
        f.write(f"Slot:        #{slot:05d}\n")
        f.write(f"Private Key: {private_key}\n\n")
        f.write(f"Attempts:    {attempts:,}\n")
        f.write(f"Time:        {elapsed:.1f}s\n\n")
        f.write("Go to https://xdead.xyz/mint and paste the private key.\n")
        f.write("The key is processed in your browser — never sent to any server.\n")
    return filename


def worker(worker_id: int, found_queue: multiprocessing.Queue, stop_event: multiprocessing.Event):
    """Worker process: generate keys until a match is found."""
    attempts = 0
    start = time.time()

    while not stop_event.is_set():
        pk_bytes = os.urandom(32)
        try:
            pk = eth_keys.PrivateKey(pk_bytes)
            address = pk.public_key.to_checksum_address()
        except Exception:
            continue
        private_key = "0x" + pk_bytes.hex()
        attempts += 1

        slot = check_address(address)
        if slot is not None:
            elapsed = time.time() - start
            found_queue.put({
                "address": address,
                "slot": slot,
                "private_key": private_key,
                "attempts": attempts,
                "elapsed": elapsed,
                "worker_id": worker_id,
            })
            return

        # Report progress every 5000 attempts
        if attempts % 5000 == 0:
            elapsed = time.time() - start
            rate = attempts / elapsed if elapsed > 0 else 0
            found_queue.put({"progress": True, "worker_id": worker_id, "attempts": attempts, "rate": rate})


def run_single():
    print()
    print("  xDead Wallet Finder — single core")
    print("  Target: 0xdead00001 — 0xdead10000")
    print("  Press Ctrl+C to stop")
    print()

    attempts = 0
    start = time.time()
    found_count = 0

    try:
        while True:
            pk_bytes = os.urandom(32)
            try:
                pk = eth_keys.PrivateKey(pk_bytes)
                address = pk.public_key.to_checksum_address()
            except Exception:
                continue
            private_key = "0x" + pk_bytes.hex()
            attempts += 1

            slot = check_address(address)
            if slot is not None:
                elapsed = time.time() - start
                found_count += 1

                print(f"\n{'=' * 50}")
                print(f"  FOUND! #{found_count}")
                print(f"  Address:     {address}")
                print(f"  Slot:        #{slot:05d}")
                print(f"  Private Key: {private_key}")
                print(f"  Attempts:    {attempts:,}")
                print(f"  Time:        {elapsed:.1f}s")
                print(f"{'=' * 50}")

                filename = save_result(address, slot, private_key, attempts, elapsed)
                print(f"  Saved to: {filename}")
                print()
                print("  Continuing search for more... (Ctrl+C to stop)")
                print()

            if attempts % 2000 == 0:
                elapsed = time.time() - start
                rate = attempts / elapsed if elapsed > 0 else 0
                print(f"\r  Attempts: {attempts:>10,}  |  Speed: {rate:>8,.0f}/s  |  Found: {found_count}", end="", flush=True)

    except KeyboardInterrupt:
        elapsed = time.time() - start
        rate = attempts / elapsed if elapsed > 0 else 0
        print(f"\n\n  Stopped.")
        print(f"  Total attempts: {attempts:,}")
        print(f"  Speed:          {rate:.0f}/s")
        print(f"  Found:          {found_count}")


def run_multi(cores: int):
    print()
    print(f"  xDead Wallet Finder — {cores} cores")
    print(f"  Target: 0xdead00001 — 0xdead10000")
    print(f"  Press Ctrl+C to stop")
    print()

    found_queue = multiprocessing.Queue()
    stop_event = multiprocessing.Event()
    processes = []
    total_attempts = [0] * cores
    found_count = 0
    start = time.time()

    for i in range(cores):
        p = multiprocessing.Process(target=worker, args=(i, found_queue, stop_event), daemon=True)
        p.start()
        processes.append(p)

    try:
        while True:
            while not found_queue.empty():
                msg = found_queue.get_nowait()

                if msg.get("progress"):
                    wid = msg["worker_id"]
                    total_attempts[wid] = msg["attempts"]
                    total = sum(total_attempts)
                    elapsed = time.time() - start
                    total_rate = total / elapsed if elapsed > 0 else 0
                    print(f"\r  Attempts: {total:>10,}  |  Speed: {total_rate:>8,.0f}/s  |  Found: {found_count}", end="", flush=True)
                else:
                    # Found a match
                    elapsed = time.time() - start
                    found_count += 1
                    address = msg["address"]
                    slot = msg["slot"]
                    private_key = msg["private_key"]
                    attempts = sum(total_attempts) + msg["attempts"]

                    print(f"\n{'=' * 50}")
                    print(f"  FOUND! #{found_count}")
                    print(f"  Address:     {address}")
                    print(f"  Slot:        #{slot:05d}")
                    print(f"  Private Key: {private_key}")
                    print(f"  Attempts:    {attempts:,}")
                    print(f"  Time:        {elapsed:.1f}s")
                    print(f"{'=' * 50}")

                    filename = save_result(address, slot, private_key, attempts, elapsed)
                    print(f"  Saved to: {filename}")
                    print()
                    print("  Restarting workers for next find...")
                    print()

                    # Restart the worker that found
                    wid = msg["worker_id"]
                    processes[wid].terminate()
                    p = multiprocessing.Process(target=worker, args=(wid, found_queue, stop_event), daemon=True)
                    p.start()
                    processes[wid] = p

            time.sleep(0.1)

    except KeyboardInterrupt:
        stop_event.set()
        for p in processes:
            p.terminate()
        total = sum(total_attempts)
        elapsed = time.time() - start
        rate = total / elapsed if elapsed > 0 else 0
        print(f"\n\n  Stopped.")
        print(f"  Total attempts: {total:,}")
        print(f"  Speed:          {rate:.0f}/s")
        print(f"  Found:          {found_count}")


def main():
    parser = argparse.ArgumentParser(description="xDead Wallet Finder")
    parser.add_argument("--cores", type=int, default=1,
                        help="Number of CPU cores to use (default: 1)")
    args = parser.parse_args()

    cores = max(1, min(args.cores, multiprocessing.cpu_count()))

    print()
    print("=" * 50)
    print("        xDead Wallet Finder v1.0")
    print("   https://github.com/xDeadProject/xDead-finder")
    print("=" * 50)

    if cores > 1:
        run_multi(cores)
    else:
        run_single()


if __name__ == "__main__":
    main()
