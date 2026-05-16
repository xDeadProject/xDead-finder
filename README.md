# xDead Wallet Finder

A script that generates random Ethereum wallets and searches for addresses matching the pattern **0xdead00001 — 0xdead20000**.

When found — saves the private key and address to a `.txt` file. Bring that key to [xdead.xyz/mint](https://xdead.xyz/mint) to claim 100 $DEAD for 0.001 ETH.

---

## How it works

The script generates random private keys, derives the Ethereum address, and checks if it starts with `0xdead` followed by a 5-digit number between `00001` and `20000`. On average you'll find one every **3–5 million attempts** (~5–15 minutes on a modern CPU).

---

## Requirements

- Python 3.10+
- pip

---

## Install & Run

**1. Download the script**

```bash
git clone https://github.com/xDeadProject/xDead-finder.git
cd xdead-finder
```

Or just download `xdead_finder.py` directly.

**2. Install dependencies**

```bash
pip install eth-account
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

## Example output

```
==================================================
        xDead Wallet Finder v1.0
==================================================

  Attempts:  3,847,221  |  Speed:  42,150/s  |  Found: 0

==================================================
  FOUND! #1
  Address:     0xDEaD00042a3F1c8E4b2D9f7A...
  Slot:        #00042
  Private Key: 0xabc123...
  Attempts:    3,847,221
  Time:        91.3s
==================================================
  Saved to: found_slot_00042.txt
```

The private key is saved to `found_slot_00042.txt` in the same folder.

---

## How to use the found key

1. Go to **[xdead.xyz/mint](https://xdead.xyz/mint)**
2. Paste the private key from the `.txt` file
3. The key is processed **entirely in your browser** — never sent to any server
4. Follow the steps: tweet → connect wallet → pay 0.001 ETH → receive 100 $DEAD

---

## Speed tips

| Method | Speed |
|---|---|
| `python xdead_finder.py` | ~10,000–50,000/s |
| `python xdead_finder.py --cores 4` | ~40,000–200,000/s |
| `python xdead_finder.py --cores 8` | ~80,000–400,000/s |

Check your CPU core count:
- Windows: Task Manager → Performance → CPU → Cores
- Mac/Linux: `nproc`

---

## Build your own version

Want to write your own finder? Here's the core logic:

```python
import os
import re
from eth_account import Account

def check_address(address):
    lower = address.lower()
    if not lower.startswith("0xdead"):
        return None
    match = re.match(r"^(\d{5})", lower[6:])
    if not match:
        return None
    num = int(match.group(1))
    return num if 1 <= num <= 20000 else None

while True:
    pk = "0x" + os.urandom(32).hex()
    account = Account.from_key(pk)
    slot = check_address(account.address)
    if slot:
        print(f"Found slot #{slot:05d}: {account.address}")
        print(f"Private key: {pk}")
        break
```

You can also ask an AI to build a faster version using:

```
Write a Python script that generates random Ethereum private keys,
derives the address using eth_account, and checks if the address starts
with "0xdead" followed by exactly 5 decimal digits forming a number
between 1 and 20000. Use multiprocessing for speed. When found, print
the address, slot number, and private key, then save to a file.
```

---

## Security

- The script runs **100% locally** on your machine
- No data is sent anywhere
- The private key of the found wallet never needs to touch the internet — xdead.xyz processes it client-side only
- The found wallet should have zero ETH — it is only used as proof of work

---

## License

MIT
