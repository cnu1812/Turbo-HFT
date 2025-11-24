import socket
import struct
import time
import random

INTERFACE_IP = "192.168.50.1"
TARGET_IP = "192.168.50.2"
PORT = 9999
FMT = "<IIQIQ"

def int_to_str(val):
    try:
        return val.to_bytes(4, 'little').decode('utf-8')
    except:
        return "????"

def run_exchange():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((INTERFACE_IP, PORT))
    sock.settimeout(0.2)

    print(f"[*] Exchange Active on {INTERFACE_IP}:{PORT}")
    print(f"[*] Broadcasting Market Data (AAPL)...")
    print("-" * 50)

    symbol = 0x4C504141 # AAPL
    i = 0
    
    # --- CHANGED: Infinite Loop ---
    while True: 
        now_ns = time.time_ns()
        price_dollars = random.randint(145, 152)
        price_micros = price_dollars * 1000000
        
        payload = struct.pack(FMT, 1, symbol, price_micros, 0, now_ns)
        sock.sendto(payload, (TARGET_IP, PORT))
        
        try:
            data, addr = sock.recvfrom(1024)
            rx_time = time.time_ns()
            msg_type, sym, p, qty, tx_ts = struct.unpack(FMT, data)
            
            if msg_type == 2: 
                latency = (rx_time - tx_ts) / 1000.0
                sym_str = int_to_str(sym)
                print(f"[{i}] PRICE: ${price_dollars}.00 -> TRADER ACTION: BUY {qty} {sym_str} (Latency: {latency:.2f}us)")
            
        except socket.timeout:
            print(f"[{i}] PRICE: ${price_dollars}.00 -> TRADER ACTION: HOLD (Too Expensive)")
        
        i += 1
        time.sleep(0.5)

if __name__ == "__main__":
    run_exchange()
