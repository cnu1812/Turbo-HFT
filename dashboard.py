import subprocess
import os
import sys
import struct
import time
import json

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_map_id(map_name):
    """Finds the ID of a BPF map by its name using JSON."""
    try:
        cmd = "sudo bpftool map show -j"
        result = subprocess.check_output(cmd, shell=True)
        maps = json.loads(result)
        for m in maps:
            if m.get('name') == map_name:
                return m['id']
    except Exception as e:
        print(f"[!] Error finding map {map_name}: {e}")
    return None

def update_map(map_name, key_int, value_int):
    """Writes values using explicit 'hex' mode to prevent parsing errors."""
    map_id = get_map_id(map_name)
    if not map_id:
        return

    # Convert to Little Endian Hex Strings
    key_bytes = struct.pack("<I", key_int)
    val_bytes = struct.pack("<Q", value_int)

    # Format: "00 00 00 00"
    key_hex = " ".join(["{:02x}".format(x) for x in key_bytes])
    val_hex = " ".join(["{:02x}".format(x) for x in val_bytes])

    # CRITICAL FIX: Added 'hex' keyword before the values
    cmd = f"sudo bpftool map update id {map_id} key hex {key_hex} value hex {val_hex}"
    
    ret = os.system(cmd)
    if ret != 0:
        print(f"[!] Failed to update map. Command: {cmd}")

def read_map(map_name, key_int):
    """Reads values using JSON mode (-j) for safety."""
    map_id = get_map_id(map_name)
    if not map_id: return 0

    key_bytes = struct.pack("<I", key_int)
    key_hex = " ".join(["{:02x}".format(x) for x in key_bytes])

    # CRITICAL FIX: Use -j for JSON output
    cmd = f"sudo bpftool map lookup id {map_id} key hex {key_hex} -j"
    try:
        output = subprocess.check_output(cmd, shell=True).decode().strip()
        data = json.loads(output)
        
        # bpftool returns value as a list of strings like ["0x80", "0xd1", ...]
        # or sometimes "formatted" values. We need the raw "value" array.
        if "value" in data:
            # value is usually a list of hex strings ["0x00", "0x00"...]
            # Convert properly based on format
            val_list = data["value"]
            if isinstance(val_list, list):
                # Convert ["0x80", "0x01"] -> bytes
                hex_bytes = bytes([int(x, 16) for x in val_list])
                return struct.unpack("<Q", hex_bytes)[0]
    except Exception as e:
        # If key doesn't exist or other error
        pass
    return 0

def clear_screen():
    os.system('clear')

# ==========================================
# MAIN INTERFACE
# ==========================================

def run_dashboard():
    # 1. FORCE INITIALIZATION
    print("[*] Booting Engine... Setting Price to $150.00")
    update_map("config_map", 0, 150000000) 
    update_map("config_map", 1, 1)         
    time.sleep(1)

    while True:
        clear_screen()
        
        # Read Stats
        shares = read_map("stats_map", 0)
        spent_micros = read_map("stats_map", 1)
        spent = spent_micros / 1000000.0
        
        # Read Config
        target_micros = read_map("config_map", 0)
        target = target_micros / 1000000.0
        status_code = read_map("config_map", 1)
        
        status_str = "🟢 ONLINE" if status_code == 1 else "🔴 KILLED (SAFETY MODE)"

        print("==================================================")
        print("       TURBO-HFT COMMAND CENTER (v3.0)")
        print("==================================================")
        print(f" STATUS:        {status_str}")
        print(f" TARGET PRICE:  ${target:.2f}")
        print("--------------------------------------------------")
        print(f" SHARES BOUGHT: {shares}")
        print(f" CAPITAL SPENT: ${spent:,.2f}")
        print("--------------------------------------------------")
        print(" [1] Set Target Price: $148.00")
        print(" [2] Set Target Price: $155.00")
        print(" [3] KILL SWITCH")
        print(" [4] RESET STATS")
        print(" [0] Exit")
        print("==================================================")
        
        try:
            choice = input(" ENTER COMMAND > ")
        except KeyboardInterrupt:
            break

        if choice == '1':
            update_map("config_map", 0, 148000000)
            update_map("config_map", 1, 1)
        elif choice == '2':
            update_map("config_map", 0, 155000000)
            update_map("config_map", 1, 1)
        elif choice == '3':
            update_map("config_map", 1, 0)
        elif choice == '4':
            update_map("stats_map", 0, 0)
            update_map("stats_map", 1, 0)
        elif choice == '0':
            break
        
        time.sleep(0.2)

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Error: Run as sudo")
        sys.exit(1)
    run_dashboard()
