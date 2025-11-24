#!/bin/bash

ip netns del exchange_ns 2>/dev/null
ip link del veth_exch 2>/dev/null

echo "[*] Creating Network Namespaces..."
ip netns add exchange_ns

ip link add veth_exch type veth peer name veth_hft

ip link set veth_exch netns exchange_ns

ip addr add 192.168.50.2/24 dev veth_hft
ip link set veth_hft up

ip netns exec exchange_ns ip addr add 192.168.50.1/24 dev veth_exch
ip netns exec exchange_ns ip link set veth_exch up

ethtool -K veth_hft tx off rx off 2>/dev/null
ip netns exec exchange_ns ethtool -K veth_exch tx off rx off 2>/dev/null

echo "[*] Setup Complete. Interface 'veth_hft' is ready for XDP."
