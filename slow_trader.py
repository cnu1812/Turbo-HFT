import socket
import struct

# Same Protocol
FMT = "<IIQIQ"
# Listen on the IP that the Exchange sends to
BIND_IP = "192.168.50.2" 
PORT = 9999

def run_slow_bot():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((BIND_IP, PORT))
    
    print(f"[*] Slow (User-Space) Trader running on {BIND_IP}:{PORT}")
    
    while True:
        data, addr = sock.recvfrom(1024)
        
        # 1. Parse the packet (User Space cost)
        msg_type, symbol, price, qty, ts = struct.unpack(FMT, data)
        
        # 2. Business Logic (Price < 150.00)
        if msg_type == 1 and symbol == 0x4C504141: # AAPL
            if price < 150000000:
                
                # 3. Create Buy Order
                # We keep the timestamp from the incoming packet to measure RTT
                response = struct.pack(FMT, 2, symbol, price, 1000, ts)
                
                # 4. Send it back (Syscall cost)
                sock.sendto(response, addr)
                # print("Executed trade in User Space")

if __name__ == "__main__":
    run_slow_bot()
