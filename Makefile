TARGET := xdp_hft.o
SRC := xdp_hft.c

# 1. Detect Architecture (x86_64)
ARCH := $(shell uname -m | sed 's/x86_64/x86/')

# 2. Find the architecture-specific include path (Where asm/types.h lives)
# On Ubuntu/Debian this is usually /usr/include/x86_64-linux-gnu
INCLUDES := -I/usr/include/$(shell uname -m)-linux-gnu

# 3. Compiler Flags
# We add $(INCLUDES) so clang can find asm/types.h
BPF_CFLAGS := -O2 -g -target bpf -D__TARGET_ARCH_$(ARCH) $(INCLUDES)

all: $(TARGET)

$(TARGET): $(SRC) protocol.h
	clang $(BPF_CFLAGS) -c $(SRC) -o $(TARGET)

clean:
	rm -f *.o
