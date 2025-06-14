# ------------------------------
# Purpose:
# - Initialize registers
# - Perform some arithmetic
# - Store to memory, load back
# - Use jalr for jump
# - Use beq and bne to test branching
# ------------------------------

# x1 = 10
addi x1, x0, 10

# x2 = x1 - 3 => 7
addi x3, x0, 3
sub x2, x1, x3

# x4 = x2 OR 0x0F => 0x0F | 7 = 0x0F
ori x4, x2, 0x0F

# x5 = x2 AND 0x06 => 7 & 6 = 6
andi x5, x2, 0x06

# x6 = (x5 < x4) ? 1 : 0 => 1
slt x6, x5, x4

# Store x4 to Mem[0x100]
addi x10, x0, 0x100  # x10 = base address
sw x4, 0(x10)        # Mem[0x100] = x4

# Load from Mem[0x100] to x7
lw x7, 0(x10)

# Branch not taken: x7 = x4 = 0x0F; x5 = 6 => not equal
beq x5, x7, +8       # Should NOT jump (x5 ≠ x7)

# Branch taken: x5 = 6; x2 = 7 => not equal => bne jumps
bne x5, x2, +8       # Should jump over next add

# Instruction to be skipped if branch above is taken
addi x8, x0, 0xFF    # This gets skipped if bne works

# jalr: jump to address in x10 (0x100), but add 4 offset
addi x9, x0, 4
jalr x0, x10, 4     # PC = x10 + 4 = 0x104, no return (rd = x0)

# If processor loops correctly, control jumps to lw above or next instruction.
# You may want to manually place a halt condition at memory[0x104] (if supported).
