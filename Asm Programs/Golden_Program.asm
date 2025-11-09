############################################################
# RISC-V ISA TEST PROGRAM (FIXED JALR)
############################################################

    .section .data
results:
    .space 128        # space for results
testdata:
    .word 0x12345678
    .word 0xAABBCCDD
    .byte 0x11, 0x22, 0x33, 0x44
    .align 4

    .section .text
    .globl _start
_start:

############################################################
# Initialize registers using only ADDI (no LI pseudo)
############################################################
    addi x1, x0, 7         # x1 = 7
    addi x2, x0, 3         # x2 = 3
    addi x3, x0, -8        # x3 = -8
    addi x4, x0, 1         # x4 = 1
    addi x5, x0, 0         # x5 = 0
    addi x6, x0, 32        # x6 = 32
    addi x7, x0, 0         # x7 = 0

############################################################
# Address setup (no LA pseudo)
############################################################
    lui  x10, %hi(results)
    addi x10, x10, %lo(results)

    lui  x11, %hi(testdata)
    addi x11, x11, %lo(testdata)

############################################################
# R-TYPE INSTRUCTIONS
############################################################
    add  x12, x1, x2       # x12 = 10
    sw   x12, 0(x10)

    sub  x12, x1, x2       # x12 = 4
    sw   x12, 4(x10)

    sll  x12, x1, x2       # 7 << 3 = 56
    sw   x12, 8(x10)

    slt  x12, x3, x4       # (-8 < 1) ? 1 : 0
    sw   x12, 12(x10)

    sltu x12, x3, x4       # unsigned compare: 0xFFFFFFF8 < 1 ? 0
    sw   x12, 16(x10)

    xor  x12, x1, x2       # 7 ^ 3 = 4
    sw   x12, 20(x10)

    srl  x12, x6, x2       # 32 >> 3 = 4
    sw   x12, 24(x10)

    sra  x12, x3, x2       # -8 >> 3 = -1
    sw   x12, 28(x10)

    or   x12, x1, x2       # 7 | 3 = 7
    sw   x12, 32(x10)

    and  x12, x1, x2       # 7 & 3 = 3
    sw   x12, 36(x10)

############################################################
# I-TYPE (ALU immediate + shift immediate)
############################################################
    addi x13, x1, 5        # 7+5=12
    sw   x13, 40(x10)

    slli x13, x1, 2        # 7<<2 = 28
    sw   x13, 44(x10)

    slti x13, x1, 10       # 7<10?1
    sw   x13, 48(x10)

    sltiu x13, x1, 10      # same unsigned
    sw   x13, 52(x10)

    xori x13, x1, 6        # 7^6=1
    sw   x13, 56(x10)

    srli x13, x6, 1        # 32>>1=16
    sw   x13, 60(x10)

    srai x13, x3, 1        # -8>>1=-4
    sw   x13, 64(x10)

    ori  x13, x1, 8        # 7|8=15
    sw   x13, 68(x10)

    andi x13, x1, 1        # 7&1=1
    sw   x13, 72(x10)

############################################################
# LOAD / STORE (word, byte)
############################################################
    lw   x14, 0(x11)       # load word 0x12345678
    sw   x14, 76(x10)

    lb   x14, 8(x11)       # load byte 0x11 (sign extend)
    sw   x14, 80(x10)

    lbu  x14, 9(x11)       # load byte 0x22 (zero extend)
    sw   x14, 84(x10)

    addi x15, x0, 0x55
    sb   x15, 10(x11)      # store 0x55 at offset 10
    lb   x14, 10(x11)      # read back
    sw   x14, 88(x10)

    addi x15, x0, 0xAA
    sw   x15, 4(x11)       # store word 0xAA at offset 4
    lw   x14, 4(x11)
    sw   x14, 92(x10)

############################################################
# BRANCHES
############################################################
    addi x16, x0, 10
    addi x17, x0, 10
    addi x18, x0, 5
    addi x19, x0, -1       # 0xFFFFFFFF

    beq  x16, x17, beq_taken
    addi x20, x0, 1        # not taken
    jal  x0, beq_done
beq_taken:
    addi x20, x0, 2
beq_done:
    sw   x20, 96(x10)

    bne  x16, x18, bne_taken
    addi x20, x0, 3
    jal  x0, bne_done
bne_taken:
    addi x20, x0, 4
bne_done:
    sw   x20, 100(x10)

    blt  x18, x16, blt_taken
    addi x20, x0, 5
    jal  x0, blt_done
blt_taken:
    addi x20, x0, 6
blt_done:
    sw   x20, 104(x10)

    bge  x16, x18, bge_taken
    addi x20, x0, 7
    jal  x0, bge_done
bge_taken:
    addi x20, x0, 8
bge_done:
    sw   x20, 108(x10)

    bltu x16, x19, bltu_taken
    addi x20, x0, 9
    jal  x0, bltu_done
bltu_taken:
    addi x20, x0, 10
bltu_done:
    sw   x20, 112(x10)

    bgeu x19, x16, bgeu_taken
    addi x20, x0, 11
    jal  x0, bgeu_done
bgeu_taken:
    addi x20, x0, 12
bgeu_done:
    sw   x20, 116(x10)

############################################################
# JAL and JALR (no relocation overflow)
############################################################
    jal  x1, jal_target
    addi x21, x0, 0x10     # skipped
jal_target:
    addi x21, x0, 0x20
    sw   x21, 120(x10)

    # fixed JALR test
    addi x22, x0, 0        # rd for jalr (return address)
    auipc x23, 0            # get current PC into x23
    addi  x23, x23, 12      # add small immediate to jump forward (~3 instructions ahead)
    jalr  x22, 0(x23)       # jump to after_jalr, save PC+4 into x22

after_jalr:
    sw   x22, 124(x10)
############################################################
# U-type: LUI, AUIPC
############################################################
    lui  x24, 0x12345      # x24 = 0x12345000
    sw   x24, 128(x10)

    auipc x25, 1           # x25 = PC + 0x1000
    sw   x25, 132(x10)

############################################################
# DONE: loop forever
############################################################
done:
    jal x0, done