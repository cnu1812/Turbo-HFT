from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import subprocess
import struct
import json
import os
import time
import sys

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Global variable to track realized profit
BANK_BALANCE = 0.0

# --- HELPER FUNCTIONS ---
def get_map_id(map_name):
    try:
        cmd = "sudo bpftool map show -j"
        result = subprocess.check_output(cmd, shell=True)
        maps = json.loads(result)
        for m in maps:
            if m.get('name') == map_name:
                return m['id']
    except Exception as e:
        print(f"[!] Map find error: {e}")
    return None

def update_map(map_name, key_int, value_int):
    map_id = get_map_id(map_name)
    if not map_id: return
    key_bytes = struct.pack("<I", key_int)
    val_bytes = struct.pack("<Q", value_int)
    key_hex = " ".join(["{:02x}".format(x) for x in key_bytes])
    val_hex = " ".join(["{:02x}".format(x) for x in val_bytes])
    cmd = f"sudo bpftool map update id {map_id} key hex {key_hex} value hex {val_hex}"
    os.system(cmd)

def read_map(map_name, key_int):
    map_id = get_map_id(map_name)
    if not map_id: return 0
    key_bytes = struct.pack("<I", key_int)
    key_hex = " ".join(["{:02x}".format(x) for x in key_bytes])
    cmd = f"sudo bpftool map lookup id {map_id} key hex {key_hex} -j"
    try:
        output = subprocess.check_output(cmd, shell=True).decode().strip()
        data = json.loads(output)
        if "value" in data:
            val_list = data["value"]
            if isinstance(val_list, list):
                hex_bytes = bytes([int(x, 16) for x in val_list])
                return struct.unpack("<Q", hex_bytes)[0]
    except:
        pass
    return 0

# --- BACKGROUND TASK ---
def stats_loop():
    print("[*] Background Stats Loop Started...")
    global BANK_BALANCE
    while True:
        try:
            shares = read_map("stats_map", 0)
            spent_micros = read_map("stats_map", 1)
            target_micros = read_map("config_map", 0)
            status_code = read_map("config_map", 1)
            
            data = {
                'shares': shares,
                'spent': spent_micros / 1000000.0,
                'target': target_micros / 1000000.0,
                'status': status_code,
                'bank': BANK_BALANCE # Send Bank Balance to UI
            }
            socketio.emit('stats_update', data)
            
        except Exception as e:
            print(f"[!] Stats Loop Error: {e}")
            
        socketio.sleep(0.5)

# --- WEB ROUTES ---
@app.route('/')
def index(): return render_template('index.html')

@socketio.on('connect')
def test_connect(): print("[+] Client Connected!")

@socketio.on('set_price')
def handle_price(data):
    price = int(float(data['price']) * 1000000)
    print(f"[*] Set Price ${data['price']}")
    update_map("config_map", 0, price)
    update_map("config_map", 1, 1)

@socketio.on('kill_switch')
def handle_kill():
    print("[!] KILL SWITCH")
    update_map("config_map", 1, 0)

@socketio.on('sell_all')
def handle_sell():
    global BANK_BALANCE
    print("\n[$$$] --- EXECUTING LIQUIDATION STRATEGY ---")
    
    # 1. Read the latest stats from the Kernel
    shares = read_map("stats_map", 0)
    cost_micros = read_map("stats_map", 1)
    
    if shares > 0:
        # 2. Determine Sell Price 
        # We assume we sell at $155.00 to show off a profit.
        sell_price_dollars = 155.00 
        sell_price_micros = int(sell_price_dollars * 1000000)
        
        # 3. Calculate Revenue 
        revenue_micros = shares * sell_price_micros
        
        # 4. Calculate Net Profit 
        # Profit = Revenue - Cost
        profit_micros = revenue_micros - cost_micros
        
        # Convert to Dollars for the Bank
        revenue_dollars = revenue_micros / 1000000.0
        cost_dollars = cost_micros / 1000000.0
        profit_dollars = profit_micros / 1000000.0
        
        # Update the Global Bank Balance
        BANK_BALANCE += profit_dollars

        # 5. DETAILED LOGGING 
        print(f" [>] SHARES SOLD:   {shares}")
        print(f" [>] EXECUTION IMG: ${sell_price_dollars:.2f}")
        print(f" [>] TOTAL REVENUE: ${revenue_dollars:,.2f}")
        print(f" [>] CAPITAL SPENT: ${cost_dollars:,.2f}")
        print("-" * 30)
        print(f" [=] NET PROFIT:    ${profit_dollars:,.2f}")
        print("-" * 30)

        # 6. Reset Kernel Maps to 0 
        update_map("stats_map", 0, 0) # Reset Shares
        update_map("stats_map", 1, 0) # Reset Cost
        
        # 7. Stop buying (Safety Mode)
        update_map("config_map", 1, 0)
        
    else:
        print("[!] No shares to sell!")

# --- STARTUP ---
if __name__ == '__main__':
    print("[*] Initializing Maps...")
    update_map("config_map", 0, 150000000)
    update_map("config_map", 1, 1)
    
    socketio.start_background_task(stats_loop)
    socketio.run(app, host='0.0.0.0', port=5000)
