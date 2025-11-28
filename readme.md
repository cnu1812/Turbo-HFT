# ⚡ Turbo-HFT: Kernel-Bypass Trading Engine

**eBPF Summit Hackathon 2025 Submission**

Turbo-HFT is an ultra-low-latency trading engine that runs **entirely inside the Linux Kernel networking path** using XDP. By processing market data and executing orders at the driver level, we eliminate the overhead of the OS network stack and context switching.


## 🛑 The Problem
In modern High-Frequency Trading (HFT), the Operating System is the bottleneck.
* **Context Switches:** Moving data from Kernel to User Space takes time.
* **Network Stack:** The Linux TCP/IP stack is designed for compatibility, not raw speed.
* **Latency:** A standard Python bot has a round-trip time of **~1500µs**.

## 💡 The Solution
Turbo-HFT moves the trading strategy **into the NIC driver**.
* **Zero-Copy Execution:** We parse NASDAQ-style packets and trigger "Buy" orders inside the XDP hook.
* **Live Kernel Control:** Using eBPF Maps, we can dynamically adjust "Target Prices" or trigger a "Kill Switch" from userspace without recompiling.
* **Performance:** Achieves **~300µs** latency in a virtualized environment (estimated <10µs on bare metal).

## 🕹️ Two Ways to Control
Turbo-HFT offers dual-mode command and control. Choose your weapon:

### 1. The Web Terminal 
A full-featured dashboard with real-time Chart.js visualization, scrolling event logs, and bank balance tracking.

![web](https://github.com/user-attachments/assets/3cc69239-f169-424a-9988-a72d7e0bd507)


### 2. The CLI Commander
A lightweight, text-based interface for raw, low-overhead monitoring directly in the terminal.

![terminal](https://github.com/user-attachments/assets/0f623313-bd92-419f-828a-5b57ee1400d9)


## 🛠️ The Tech Stack
* **Data Plane:** C (XDP/eBPF) - The "Muscle"
* **Control Plane:** Python (BCC/bpftool/Flask) - The "Brain"
* **Frontend:** HTML5, Bootstrap 5, Chart.js, WebSockets
* **Features:**
    * Deep Packet Inspection (DPI) on UDP payloads.
    * Dynamic Quantity Scaling (Buys more when price is lower).
    * **Live Liquidation Logic:** Real-time P&L calculation on "Sell" orders.

## 🚀 How to Run

### Part 1: Core Setup 
First, compile the kernel code and set up the virtual network.

```bash
# 1. Build the Kernel Object
make

# 2. Setup Network Namespace 
sudo ./setup_env.sh

# 3. Load XDP Engine into the Kernel
sudo ip link set dev veth_hft xdpgeneric obj xdp_hft.o sec xdp

# 4. Start the Exchange Simulator (in a separate terminal)
sudo ip netns exec exchange_ns python3 exchange_sim.py

```
### Part 2: Choose Your Interface
#### Option A: Web Console
```
# Install dependencies
pip3 install flask flask-socketio eventlet

# Run the Server (Must be root to access BPF Maps)
sudo ./venv/bin/python3 web_server.py
```
Open your browser: Go to `http://localhost:5000`

#### Option B: The CLI Dashboard

`sudo python3 dashboard.py`

## 🏆 Benchmark Verification
| System | Architecture | Latency (RTT) |
| :--- | :--- | :--- |
| **Standard Bot** | Python `recv()` Loop | ~1520 µs |
| **Turbo-HFT** | **eBPF XDP Hook** | **~280 µs** |
| **Speedup** | | **~5.4x Faster** |
