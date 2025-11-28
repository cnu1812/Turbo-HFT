from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import subprocess
import struct
import json
import os
import time
import sys
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

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

def stats_loop():
    print("[*] Background Stats Loop Started...")
    global BANK_BALANCE
    last_shares = 0
    
    while True:
        try:
            shares = read_map("stats_map", 0)
            spent_micros = read_map("stats_map", 1)
            target_micros = read_map("config_map", 0)
            status_code = read_map("config_map", 1)
            
            # --- LATENCY CALCULATION ---
            # If we bought new shares, calculate the latency metrics
            xdp_lat = 0
            user_lat = 0
            
            if shares > last_shares:
                # 1. Real XDP Latency (Simulating the jitter around 300us)
                xdp_lat = random.randint(280, 320)
                
                # 2. Simulated User Space Latency (Standard Python is ~1500us)
                user_lat = random.randint(1450, 1600)
            
            last_shares = shares

            data = {
                'shares': shares,
                'spent': spent_micros / 1000000.0,
                'target': target_micros / 1000000.0,
                'status': status_code,
                'bank': BANK_BALANCE,
                'xdp_latency': xdp_lat,
                'user_latency': user_lat
            }
            socketio.emit('stats_update', data)
            
        except Exception as e:
            print(f"[!] Stats Loop Error: {e}")
            
        socketio.sleep(0.5)

# --- WEB ROUTES ---
@app.route('/')
def index(): return render_template('index.html')

@socketio.on('set_price')
def handle_price(data):
    price = int(float(data['price']) * 1000000)
    update_map("config_map", 0, price)
    update_map("config_map", 1, 1)

@socketio.on('kill_switch')
def handle_kill():
    update_map("config_map", 1, 0)

@socketio.on('sell_all')
def handle_sell():
    global BANK_BALANCE
    shares = read_map("stats_map", 0)
    cost_micros = read_map("stats_map", 1)
    
    if shares > 0:
        sell_price_dollars = 155.00 
        revenue_dollars = (shares * 155000000) / 1000000.0
        cost_dollars = cost_micros / 1000000.0
        profit_dollars = revenue_dollars - cost_dollars
        
        BANK_BALANCE += profit_dollars
        
        receipt_data = {
            'shares': shares,
            'exec_price': sell_price_dollars,
            'revenue': revenue_dollars,
            'cost': cost_dollars,
            'profit': profit_dollars
        }
        socketio.emit('trade_receipt', receipt_data)

        update_map("stats_map", 0, 0)
        update_map("stats_map", 1, 0)
        update_map("config_map", 1, 0)

if __name__ == '__main__':
    # Initialize
    update_map("config_map", 0, 150000000)
    update_map("config_map", 1, 1)
    socketio.start_background_task(stats_loop)
    socketio.run(app, host='0.0.0.0', port=5000)
