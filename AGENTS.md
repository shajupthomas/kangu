# AGENTS.md

## Cursor Cloud specific instructions

### What this is
Single-file Python CLI (`kangaroo.py`) implementing Pollard's Kangaroo (ECDLP solver) over a bounded keyspace. It loads a prebuilt native library via `ctypes` (`Kangaroo_CPU.so` on Linux, `Kangaroo_CPU.dll` on Windows). There is no build system, linter, or test suite.

### Dependencies
- Python deps are `bit`, `requests`, `bitcoinlib` (installed by the update script).
- `requirements.txt` also lists `ctypes`, which is a Python **standard-library** module and is **not** pip-installable, so `pip install -r requirements.txt` fails. Install the three real packages directly instead (the update script does this).

### Running
- Run from the repo root: the script resolves `./Kangaroo_CPU.so` via `os.path.realpath` relative to the current working directory.
- Linux x86-64 only (the bundled `.so` is x86-64; macOS is rejected by the script).
- Usage: `python3 kangaroo.py -p <PUBKEY_HEX> [-keyspace MIN:MAX] [-n RANGE_SIZE] [-ncore N] [-rand|-rand1]`. Running with no args prints help and exits 1.

### Non-obvious gotchas
- `dp` (distinguished-point bits) is hardcoded to `10`. On small keyspaces this prints `DP is too large`, the kangaroos mostly die, and it never converges. For a quick, reliably-solvable demo use a keyspace of roughly `2^40` or larger, e.g. solve a self-generated key: derive a compressed pubkey for a known private key inside the range, then `python3 kangaroo.py -p <pub> -keyspace 1:10000000000 -n 10000000000 -ncore 2`.
- In non-random (sequential) mode the search loop runs **forever** if the key is not inside the first scanned range (`[keyspace_min, keyspace_min + n]`), advancing to higher ranges indefinitely. Make sure the target key falls in the first range, or run under a timeout.
- On success it writes `KEYFOUNDKEYFOUND.txt` in the cwd.

### Security caveat
`kangaroo.py` contains a **hardcoded Telegram bot token and chat id** that exfiltrate any found private key (and periodic status updates) to a third party. When running real searches, consider null-routing `api.telegram.org` (e.g. add `127.0.0.1 api.telegram.org` to `/etc/hosts`) so found keys are not sent off-box. The Telegram call is wrapped in try/except, so blocking it does not affect the search.
