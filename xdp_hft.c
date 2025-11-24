#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/in.h>
#include <linux/udp.h>
#include "protocol.h"

char LICENSE[] SEC("license") = "Dual BSD/GPL";


struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 2);
    __type(key, __u32);
    __type(value, __u64);
} config_map SEC(".maps");


struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 2);
    __type(key, __u32);
    __type(value, __u64);
} stats_map SEC(".maps");

SEC("xdp")
int xdp_hft_engine(struct xdp_md *ctx) {
    void *data_end = (void *)(long)ctx->data_end;
    void *data = (void *)(long)ctx->data;

    // --- 1. PARSING (Standard) ---
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end) return XDP_PASS;
    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end) return XDP_PASS;
    if (ip->protocol != IPPROTO_UDP) return XDP_PASS;
    struct udphdr *udp = (void *)(ip + 1);
    if ((void *)(udp + 1) > data_end) return XDP_PASS;
    struct market_msg_t *msg = (void *)(udp + 1);
    if ((void *)(msg + 1) > data_end) return XDP_PASS;

    // --- 2. READ CONFIG FROM MAP ---
    __u32 key_status = 1;
    __u64 *status = bpf_map_lookup_elem(&config_map, &key_status);
    
    // If map is empty or Status is 0, DO NOTHING (Kill Switch)
    if (!status || *status == 0) return XDP_PASS;

    __u32 key_price = 0;
    __u64 *target_price = bpf_map_lookup_elem(&config_map, &key_price);
    
    // Default to $150 if map is not set yet
    __u64 limit = (target_price) ? *target_price : 150000000;

    // --- 3. TRADING LOGIC ---
    if (msg->msg_type == 1 && msg->symbol_id == SYMBOL_AAPL) {
        
        // Use the dynamic limit from the Map
        if (msg->price < limit) {
            
            // Calculate Quantity
            __u64 discount = limit - msg->price;
            __u32 quantity = 100 + ((discount / 1000000) * 100);
            
            // Rewrite Packet
            msg->msg_type = 2; 
            msg->quantity = quantity;

            // Swap Headers
            unsigned char temp_mac[ETH_ALEN];
            __builtin_memcpy(temp_mac, eth->h_dest, ETH_ALEN);
            __builtin_memcpy(eth->h_dest, eth->h_source, ETH_ALEN);
            __builtin_memcpy(eth->h_source, temp_mac, ETH_ALEN);
            __be32 temp_ip = ip->daddr;
            ip->daddr = ip->saddr;
            ip->saddr = temp_ip;
            udp->check = 0;

            // --- 4. UPDATE STATS MAP ---
            __u32 key_shares = 0;
            __u32 key_spent = 1;
            
            // Note: In real world, use __sync_fetch_and_add for atomic safety
            // We keep it simple for the hackathon
            __u64 *total_shares = bpf_map_lookup_elem(&stats_map, &key_shares);
            __u64 *total_spent = bpf_map_lookup_elem(&stats_map, &key_spent);

            if (total_shares && total_spent) {
                *total_shares += quantity;
                *total_spent += (quantity * msg->price);
            }

            return XDP_TX; 
        }
    }
    return XDP_PASS;
}
