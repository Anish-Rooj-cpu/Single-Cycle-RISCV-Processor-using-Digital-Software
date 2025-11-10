# factorial(n):
# Input:  n in x10
# Output: factorial(n) in x11
# Uses:   stack pointer (x2), return address (x1)

# -----------------------------------
# main:
# -----------------------------------
main:
    addi x10, x0, 4        # n = 5   <-- set your input here
    addi x2, x0, 200       # initialize stack pointer (arbitrary address)
    jal  x1, factorial     # call factorial(n)
    jal  x0, done          # infinite loop (halt)

# -----------------------------------
# factorial function:
# -----------------------------------
factorial:
    # Prologue
    addi x2, x2, -8        # allocate stack space
    sw   x1, 4(x2)         # store return address
    sw   x10, 0(x2)        # store n

    # Base case: if n <= 1 return 1
    addi x12, x0, 1
    slt  x13, x10, x12     # x13 = 1 if n < 1
    bne  x13, x0, base_case
    beq  x10, x12, base_case

    # Recursive case:
    addi x10, x10, -1      # n = n - 1
    jal  x1, factorial     # call factorial(n-1)

    # Restore original n from stack
    lw   x14, 0(x2)        # x14 = original n

    # Multiply n * factorial(n-1)
    mul  x11, x14, x11     # x11 = x14 * x11

    jal  x0, epilogue

base_case:
    addi x11, x0, 1        # return 1

epilogue:
    # Restore return address and release stack space
    lw   x1, 4(x2)
    addi x2, x2, 8
    jalr x0, 0(x1)        # return to caller

done:
    jal  x0, done          # stop execution (infinite loop)
