# GCD Calculator with Complete Memory Operations
# Initialization
addi x1, x0, 0x100    # x1 = 0x100 (a address)
addi x2, x0, 0x104    # x2 = 0x104 (b address)
addi x3, x0, 0x108    # x3 = 0x108 (GCD output)

# Store test values
addi x10, x0, 5       # a = 5
addi x11, x0, 1       # b = 1
sw x10, 0(x1)         # mem[0x100] = 5
sw x11, 0(x2)         # mem[0x104] = 1

# GCD Calculation
gcd_loop:
    beq x10, x11, gcd_done
    slt x12, x10, x11
    beq x12, x0, a_ge_b
    add x13, x10, x0   # swap
    add x10, x11, x0
    add x11, x13, x0
    jal x0, gcd_loop
a_ge_b:
    sub x10, x10, x11
    jal x0, gcd_loop
gcd_done:
    sw x10, 0(x3)      # Store GCD

# Division Loop Setup
addi x4, x0, 0        # Quotient = 0
addi x5, x0, 5        # Divisor = 5
add x6, x10, x0       # Dividend = GCD

div_loop:
    slt x7, x6, x5    # Remainder < divisor?
    bne x7, x0, div_done
    sub x6, x6, x5    # Subtract divisor
    addi x4, x4, 1    # Increment quotient
    jal x0, div_loop

div_done:
    sw x4, 0x10C(x0)  # Store quotient
    sw x6, 0x110(x0)  # Store remainder

# Bitwise Calculation
lw x10, 0(x1)        # Reload a
lw x11, 0(x2)        # Reload b
or x12, x10, x11
and x13, x10, x11
sub x14, x12, x13
sw x14, 0x114(x0)    # Store (a|b)-(a&b)

# Verification Point
lw x15, 0(x3)        # x15 = GCD
lw x16, 0x10C(x0)    # x16 = quotient
lw x17, 0x110(x0)    # x17 = remainder
lw x18, 0x114(x0)    # x18 = bitwise result

# Infinite loop with results in registers
halt:
add x0, x0, x0       # NOP
jal x0, halt