# ⚡ Turbo-HFT: Kernel-Bypass Trading Engine

**eBPF Summit Hackathon 2025 Submission**

Turbo-HFT is an ultra-low-latency trading engine that runs **entirely inside the Linux Kernel networking path** using XDP. By processing market data and executing orders at the driver level, we eliminate the overhead of the OS network stack and context switching.

## 🛑 The Problem
In modern High-Frequency Trading (HFT), the Operating System is the bottleneck.
1. **Context Switches:** Moving data from Kernel to User Space takes time.
2. **Network Stack:** The Linux TCP/IP stack is designed for compatibility, not raw speed.
3. **Latency:** A standard Python bot has a round-trip time of **~1500µs**.

## 💡 The Solution
Turbo-HFT moves the trading strategy **into the NIC driver**.
* **Zero-Copy Execution:** We parse NASDAQ-style packets and trigger "Buy" orders inside the XDP hook.
* **Live Kernel Control:** Using eBPF Maps, we can dynamically adjust "Target Prices" or trigger a "Kill Switch" from userspace without recompiling.
* **Performance:** Achieves **~300µs** latency in a virtualized environment (estimated <10µs on bare metal).

## 🕹️ The Tech Stack
* **Data Plane:** C (XDP/eBPF) - The "Muscle"
* **Control Plane:** Python (BCC/bpftool) - The "Brain"
* **Features:**
    * Deep Packet Inspection (DPI) on UDP payloads.
    * Dynamic Quantity Scaling (Buys more when price is lower).
    * Live "Profit & Loss" Dashboard via BPF Maps.

## 🚀 How to Run
1.  **Build the Kernel Object:** `make`
2.  **Setup Network Namespace:** `sudo ./setup_env.sh`
3.  **Load XDP Engine:** `sudo ip link set dev veth_hft xdpgeneric obj xdp_hft.o sec xdp`
4.  **Run Exchange Simulator:** `sudo ip netns exec exchange_ns python3 exchange_sim.py`
5.  **Launch Dashboard:** `sudo python3 dashboard.py`

## 🏆 Benchmark Verification
| System | Architecture | Latency (RTT) |
| :--- | :--- | :--- |
| **Standard Bot** | Python `recv()` Loop | ~1520 µs |
| **Turbo-HFT** | **eBPF XDP Hook** | **~280 µs** |
| **Speedup** | | **~5.4x Faster** |
