import socket
import struct

FMT = "<IIQIQ"
BIND_IP = "192.168.50.2" 
PORT = 9999

def run_slow_bot():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((BIND_IP, PORT))
    
    print(f"[*] Slow (User-Space) Trader running on {BIND_IP}:{PORT}")
    
    while True:
        data, addr = sock.recvfrom(1024)
        
       
        msg_type, symbol, price, qty, ts = struct.unpack(FMT, data)
        
        
        if msg_type == 1 and symbol == 0x4C504141: # AAPL
            if price < 150000000:
                
                
                response = struct.pack(FMT, 2, symbol, price, 1000, ts)
                
                
                sock.sendto(response, addr)
                

if __name__ == "__main__":
    run_slow_bot()
