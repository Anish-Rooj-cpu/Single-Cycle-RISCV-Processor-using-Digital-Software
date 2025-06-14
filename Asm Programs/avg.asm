# Base address for array: 0x100 (assume memory is already initialized)
addi x1, x0, 0x100     # x1 = base address
addi x2, x0, 5         # x2 = count

# Load 5 integers into x10-x14
lw x10, 0(x1)          # x10 = mem[0]
lw x11, 4(x1)          # x11 = mem[1]
lw x12, 8(x1)          # x12 = mem[2]
lw x13, 12(x1)         # x13 = mem[3]
lw x14, 16(x1)         # x14 = mem[4]

# Initialize max and min
add x20, x10, x0       # x20 = max
add x21, x10, x0       # x21 = min

# Check x11 for max/min
slt x15, x20, x11      # if x20 < x11, x15 = 1
beq x15, x0, skip1
add x20, x11, x0       # max = x11
skip1:
slt x15, x11, x21      # if x11 < min, x15 = 1
beq x15, x0, skip2
add x21, x11, x0       # min = x11
skip2:

# Check x12 for max/min
slt x15, x20, x12
beq x15, x0, skip3
add x20, x12, x0
skip3:
slt x15, x12, x21
beq x15, x0, skip4
add x21, x12, x0
skip4:

# Check x13
slt x15, x20, x13
beq x15, x0, skip5
add x20, x13, x0
skip5:
slt x15, x13, x21
beq x15, x0, skip6
add x21, x13, x0
skip6:

# Check x14
slt x15, x20, x14
beq x15, x0, skip7
add x20, x14, x0
skip7:
slt x15, x14, x21
beq x15, x0, skip8
add x21, x14, x0
skip8:

# Compute sum = x10 + x11 + x12 + x13 + x14
add x22, x10, x11
add x22, x22, x12
add x22, x22, x13
add x22, x22, x14

# Divide sum by 5 via loop (repeated subtraction)
addi x23, x0, 0        # quotient = 0
add x24, x22, x0       # temp = sum
addi x25, x0, 5        # divisor = 5

div_loop:
slt x26, x24, x25      # if temp < divisor, exit
bne x26, x0, div_done
sub x24, x24, x25
addi x23, x23, 1
jal x0, div_loop

div_done:
# Result in x23 = average

# Store max at 0x120, min at 0x124, avg at 0x128
addi x1, x0, 0x120     # x1 = 0x120
sw x20, 0(x1)          # store max
sw x21, 4(x1)          # store min
sw x23, 8(x1)          # store avg

# Infinite loop (halt)
addi x0, x0, 0
jal x0, -4
