# -*- coding: utf-8 -*-

import bit
import ctypes
import platform
import sys
import os
import random
import argparse
import signal
import requests
import time
from bitcoinlib.keys import Key  # 🚀 Added for WIF conversion

###############################################################################
# 📌 TELEGRAM BOT CONFIGURATION
TELEGRAM_BOT_TOKEN = "8679246064:AAEcDr4aemgxylyR-N28iloU0t2T4UGFvaw"  # Replace with your bot token
TELEGRAM_CHAT_ID = "892100588"  # Replace with your Telegram chat ID

def send_telegram_message(message):
    """
    Sends a message to your Telegram chat.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")

###############################################################################
# 📌 ARGUMENT PARSING
parser = argparse.ArgumentParser(description='Kangaroo Algorithm for Private Key Search',
                                 epilog='Enjoy! :)    Tips BTC: bc1q39meky2mn5qjq704zz0nnkl0v7kj4uz6r529at')
parser.version = '15112021'
parser.add_argument("-p", "--pubkey", help="Public Key in hex format (compressed or uncompressed)", required=True)
parser.add_argument("-keyspace", help="Keyspace Range (hex) to search from min:max", action='store')
parser.add_argument("-ncore", help="Number of CPU cores to use", action='store')
parser.add_argument("-n", help="Total range search in one loop", action='store')
parser.add_argument("-rand", help="Start from a random value", action="store_true")
parser.add_argument("-rand1", help="Start randomly, then go sequential", action="store_true")

if len(sys.argv) == 1:
    parser.print_help()
    sys.exit(1)
args = parser.parse_args()

###############################################################################
# 📌 INITIAL SETUP
ss = args.keyspace if args.keyspace else '1:FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364140'
flag_random = args.rand or False
flag_random1 = args.rand1 or False
ncore = int(args.ncore) if args.ncore else os.cpu_count() - 1
increment = int(args.n) if args.n else 72057594037927935
public_key = args.pubkey

if flag_random1:
    flag_random = True  # Ensure `flag_random1` enables random mode

a, b = map(lambda x: int(x, 16), ss.split(':'))
lastitem = 0  # Used for sequential key searching

###############################################################################
# 📌 LOAD KANGAROO DLL (Windows / Linux)
if platform.system().lower().startswith('win'):
    pathdll = os.path.realpath('Kangaroo_CPU.dll')
    ice = ctypes.CDLL(pathdll)
elif platform.system().lower().startswith('lin'):
    pathdll = os.path.realpath('Kangaroo_CPU.so')
    ice = ctypes.CDLL(pathdll)
else:
    print('[-] Unsupported Platform. Only Windows and Linux are supported.')
    sys.exit()

ice.run_cpu_kangaroo.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p]
ice.init_kangaroo_lib()

###############################################################################
# 📌 FUNCTIONS

def run_cpu_kangaroo(start_range_int, end_range_int, dp, ncpu, mx, upub_bytes):
    st_hex = hex(start_range_int)[2:].encode('utf8')
    en_hex = hex(end_range_int)[2:].encode('utf8')
    res = (b'\x00') * 32
    ice.run_cpu_kangaroo(st_hex, en_hex, dp, ncpu, mx, res, upub_bytes)
    return res

def private_key_to_wif(private_key_hex):
    """
    Convert a private key (hex) to WIF (Wallet Import Format).
    """
    key = Key(private_key_hex)
    return key.wif()

def pub2upub(pub_hex):
    x = int(pub_hex[2:66], 16)
    if len(pub_hex) < 70:
        y = bit.format.x_to_y(x, int(pub_hex[:2], 16) % 2)
    else:
        y = int(pub_hex[66:], 16)
    return bytes.fromhex('04' + hex(x)[2:].zfill(64) + hex(y)[2:].zfill(64))

def randk(a, b):
    if flag_random:
        random.seed(random.randint(1, 2**256))
        return random.SystemRandom().randint(a, b)
    else:
        return lastitem + 1 if lastitem else a

###############################################################################
# 📌 START SEARCHING
print('[+] Starting CPU Kangaroo.... Please Wait     Version [', parser.version, ']')

dp = 10
mx = 2
upub = pub2upub(public_key)  # 🚀 Fix: Initialize upub before use

range_st = randk(a, b)  # 🚀 Fix: Initialize range_st properly
range_en = range_st + increment

print('[+] Search Mode:', 'Random Start then Continuous' if flag_random1 else 
                       'Random Start every cycle' if flag_random else 
                       'Continuous Range Search')
print('[+] Working on Pubkey:', upub.hex())
print(f'[+] Using CPU Threads: {ncore}, DP size: {dp}, MaxStep: {mx}')

###############################################################################
# 📌 SEARCH LOOP WITH TELEGRAM NOTIFICATIONS
last_update_time = time.time()

while True:
    print('\r[+] Scanning Range', hex(range_st), ':', hex(range_en))
    pvk_found = run_cpu_kangaroo(range_st, range_en, dp, ncore, mx, upub)

    if int(pvk_found.hex(), 16) != 0:
        private_key_hex = pvk_found.hex()
        wif_key = private_key_to_wif(private_key_hex)

        key_found_msg = f"🚀 KANGAROO FOUND PRIVATE KEY! 🔑\n\n"
        key_found_msg += f"📝 Private Key (HEX): 0x{private_key_hex}\n"
        key_found_msg += f"🔑 WIF Format: {wif_key}"

        print('\n============== KEY FOUND ==============')
        print(key_found_msg)
        print('======================================')

        # 🚀 FIX: Use UTF-8 encoding to prevent UnicodeEncodeError
        with open('KEYFOUNDKEYFOUND.txt', 'a', encoding='utf-8') as fw:
            fw.write(key_found_msg + '\n')

        send_telegram_message(key_found_msg)  # 🚀 Send Telegram Alert
        break  # Stop when a key is found


    if time.time() - last_update_time > 1800:
        send_telegram_message(f"📢 Still Searching...\n🔍 Range: {hex(range_st)} - {hex(range_en)}\n⚙️ CPU Cores: {ncore}")
        last_update_time = time.time()

    lastitem = range_en
    range_st = randk(a, b)
    range_en = range_st + increment
