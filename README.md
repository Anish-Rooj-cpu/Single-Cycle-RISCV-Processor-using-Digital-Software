# Single-Cycle-RISCV-Processor-using-Digital-Software
In this project I have designed and implented a Single-Cycle RISC-V Processor using the Digital Logic Simulator.
# Architecture Used :
<img width="606" alt="Risc 5 Architecture unannoted" src="https://github.com/user-attachments/assets/5759f1d1-4b0b-46fd-95f2-586a722ba84f" />

# RISC-V Base Instruction Formats 
<img width="606" alt="Risc 5 Architecture unannoted" src="https://github.com/user-attachments/assets/3016bb93-3bf9-4e93-b371-1e19e48669f2" />

# Instructions Supported
 The processor supports the **RISC-V base integer instruction set (RV32I)**, including:  
 - R-type: `add`, `sub`, `and`, `or`, `slt`, `sll`, `sltu`, `xor`, `sra`, `srl`
 - I-type: `addi`, `and`,`or`,`slti`, `lw`, `jalr`, `sltiu`, `xori`, `srai`, `srli`
 - S-type: `sw`  
 - B-type: `beq`, `bne`, `blt`, `bge`, `bltu`, `bgeu`  
 - J-type: `jal`

# Simulation 
 The Top Module or Top Block has been simulated inside the Digital Software.
 - Link of EDA Playground to see the Verilog Codes of this Processor: https://edaplayground.com/x/XeZr
 - Link to the Digital Software that has been used : https://github.com/hneemann/Digital

# Testing and Verificiation 
 The processor has been tested with various complex Programs like Factorial Determinaition, Sum of N natrual numbers, Bubble Sort and Fibonacci Series Generator.
 - A Sample Test Program has been provided (.hex file)
 - The .asm files are assembled using a custom Assembler made by Python
# How to RUN :
To Run a program using this processor, follow these steps : 
 - First, write the assembly program (with the above mentioned Instructions only, do not use any pseudo labels)
 - Then, Hardcode the input path and output path in the Assembler.py program
 - Output.v file will be generated in which there will be Hex codes hardcoded into the instruction memory
 - Copy the Hex codes and paste it to the test.hex, the ROM will automatically read the test.hex file at the starting of each run
 - Finally, run the simulation

