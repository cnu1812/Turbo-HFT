#ifndef __PROTOCOL_H
#define __PROTOCOL_H

// Little Endian representation of "AAPL"
// 'L' 'P' 'A' 'A' -> 0x4C 0x50 0x41 0x41
#define SYMBOL_AAPL 0x4C504141 

struct market_msg_t {
    __u32 msg_type;     // 1 = PRICE_UPDATE, 2 = BUY_ORDER
    __u32 symbol_id;    // "AAPL"
    __u64 price;        // Price in micros
    __u32 quantity;     // Number of shares
    __u64 timestamp;    // Latency tracking
} __attribute__((packed));

#endif
