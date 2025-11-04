import argparse
import sys
import os
import re

# === Configuration: hardcoded paths (optional) ===
# If these are non-empty strings and point to valid file/dir, they will be used.
# Otherwise fall back to CLI args or interactive prompt.
HARDCODE_INPUT_PATH = r"E:\RISCV Single Cycle Processor using Digital Software\Asm Programs\pixel2.asm"
HARDCODE_OUTPUT_PATH = r"E:\RISCV Single Cycle Processor using Digital Software\test Programs\pixel2.v"
# No hardcoded hex path by default; you may set HARDCODE_HEX_PATH similarly if desired.
HARDCODE_HEX_PATH = r"E:\RISCV Single Cycle Processor using Digital Software\Test Programs\test.hex"


# === Instruction definitions ===
R_TYPE = {
    'add':  {'funct7': 0b0000000, 'funct3': 0b000, 'opcode': 0b0110011},
    'sub':  {'funct7': 0b0100000, 'funct3': 0b000, 'opcode': 0b0110011},
    'sll':  {'funct7': 0b0000000, 'funct3': 0b001, 'opcode': 0b0110011},
    'slt':  {'funct7': 0b0000000, 'funct3': 0b010, 'opcode': 0b0110011},
    'sltu': {'funct7': 0b0000000, 'funct3': 0b011, 'opcode': 0b0110011},
    'xor':  {'funct7': 0b0000000, 'funct3': 0b100, 'opcode': 0b0110011},
    'srl':  {'funct7': 0b0000000, 'funct3': 0b101, 'opcode': 0b0110011},
    'sra':  {'funct7': 0b0100000, 'funct3': 0b101, 'opcode': 0b0110011},
    'or':   {'funct7': 0b0000000, 'funct3': 0b110, 'opcode': 0b0110011},
    'and':  {'funct7': 0b0000000, 'funct3': 0b111, 'opcode': 0b0110011},

    # RV32M extension
    'mul':  {'funct7': 0b0000001, 'funct3': 0b000, 'opcode': 0b0110011},
    'div':  {'funct7': 0b0000001, 'funct3': 0b100, 'opcode': 0b0110011},
    'rem':  {'funct7': 0b0000001, 'funct3': 0b110, 'opcode': 0b0110011},
}


I_TYPE = {
    'addi':  {'opcode': 0b0010011, 'funct3': 0b000},
    'andi':  {'opcode': 0b0010011, 'funct3': 0b111},
    'ori':   {'opcode': 0b0010011, 'funct3': 0b110},
    'xori':  {'opcode': 0b0010011, 'funct3': 0b100},
    'slti':  {'opcode': 0b0010011, 'funct3': 0b010},
    'sltiu': {'opcode': 0b0010011, 'funct3': 0b011},
    # shift-immediate: funct7 needed for slli/srli/srai
    'slli':  {'opcode': 0b0010011, 'funct3': 0b001, 'funct7': 0b0000000},
    'srli':  {'opcode': 0b0010011, 'funct3': 0b101, 'funct7': 0b0000000},
    'srai':  {'opcode': 0b0010011, 'funct3': 0b101, 'funct7': 0b0100000},
    # loads/jumps
    'lw':    {'opcode': 0b0000011, 'funct3': 0b010},
    'jalr':  {'opcode': 0b1100111, 'funct3': 0b000},
}

S_TYPE = {
    'sw': {'opcode': 0b0100011, 'funct3': 0b010},
}

B_TYPE = {
    'beq':  {'opcode': 0b1100011, 'funct3': 0b000},
    'bne':  {'opcode': 0b1100011, 'funct3': 0b001},
    'blt':  {'opcode': 0b1100011, 'funct3': 0b100},
    'bge':  {'opcode': 0b1100011, 'funct3': 0b101},
    'bltu': {'opcode': 0b1100011, 'funct3': 0b110},
    'bgeu': {'opcode': 0b1100011, 'funct3': 0b111},
}

U_TYPE = {
    'lui':   {'opcode': 0b0110111},
    'auipc': {'opcode': 0b0010111},
}

J_TYPE = {
    'jal': {'opcode': 0b1101111},
}

# Regex for register parsing: x0..x31
REG_PATTERN = re.compile(r'^x([0-9]|[12][0-9]|3[01])$')

def parse_register(reg_str):
    """Parse register string 'x0'..'x31' and return integer 0..31."""
    m = REG_PATTERN.match(reg_str)
    if not m:
        raise ValueError(f"Invalid register '{reg_str}'")
    return int(m.group(1))

def parse_immediate(imm_str):
    """
    Parse immediate: decimal or hex (0x...). Returns Python int (signed or unsigned as per usage).
    Note: For branch/jump offsets, user writes label or immediate. Label-handling done separately.
    """
    try:
        # int(str, 0) handles 0x..., decimal, and also octal if prefixed.
        val = int(imm_str, 0)
    except ValueError:
        raise ValueError(f"Invalid immediate '{imm_str}'")
    return val

# === Encoding functions ===

def encode_r_type(mnemonic, rd, rs1, rs2):
    info = R_TYPE[mnemonic]
    funct7 = info['funct7'] & 0x7F
    funct3 = info['funct3'] & 0x7
    opcode = info['opcode'] & 0x7F
    return (funct7 << 25) | ((rs2 & 0x1F) << 20) | ((rs1 & 0x1F) << 15) | (funct3 << 12) | ((rd & 0x1F) << 7) | opcode

def encode_i_type(mnemonic, rd, rs1, imm):
    info = I_TYPE[mnemonic]
    funct3 = info['funct3'] & 0x7
    opcode = info['opcode'] & 0x7F
    # This handles 12-bit 2's complement
    imm12 = imm & 0xFFF if imm >= 0 else (imm + (1 << 12)) & 0xFFF
    return (imm12 << 20) | ((rs1 & 0x1F) << 15) | (funct3 << 12) | ((rd & 0x1F) << 7) | opcode

def encode_i_shift_type(mnemonic, rd, rs1, shamt):
    info = I_TYPE[mnemonic]
    funct7 = info.get('funct7', 0) & 0x7F
    funct3 = info['funct3'] & 0x7
    opcode = info['opcode'] & 0x7F
    shamt5 = shamt & 0x1F
    return (funct7 << 25) | (shamt5 << 20) | ((rs1 & 0x1F) << 15) | (funct3 << 12) | ((rd & 0x1F) << 7) | opcode

def encode_s_type(mnemonic, rs2, rs1, imm):
    info = S_TYPE[mnemonic]
    funct3 = info['funct3'] & 0x7
    opcode = info['opcode'] & 0x7F
    # FIX: Handle 12-bit 2's complement for negative immediates
    imm12 = imm & 0xFFF if imm >= 0 else (imm + (1 << 12)) & 0xFFF
    imm11_5 = (imm12 >> 5) & 0x7F
    imm4_0  = imm12 & 0x1F
    return (imm11_5 << 25) | ((rs2 & 0x1F) << 20) | ((rs1 & 0x1F) << 15) | (funct3 << 12) | (imm4_0 << 7) | opcode

def encode_b_type(mnemonic, rs1, rs2, imm):
    info = B_TYPE[mnemonic]
    funct3 = info['funct3'] & 0x7
    opcode = info['opcode'] & 0x7F
    # imm is byte offset (can be negative). Must be multiple of 2; lower bit always zero in encoding.
    # This correctly handles 13-bit 2's complement
    imm13 = imm & 0x1FFF if imm >= 0 else (imm + (1 << 13)) & 0x1FFF
    bit12 = (imm13 >> 12) & 0x1
    bits10_5 = (imm13 >> 5) & 0x3F
    bits4_1 = (imm13 >> 1) & 0xF
    bit11 = (imm13 >> 11) & 0x1
    return (bit12 << 31) | (bits10_5 << 25) | ((rs2 & 0x1F) << 20) | ((rs1 & 0x1F) << 15) | (funct3 << 12) | (bits4_1 << 8) | (bit11 << 7) | opcode

def encode_u_type(mnemonic, rd, imm):
    info = U_TYPE[mnemonic]
    opcode = info['opcode'] & 0x7F
    imm20 = (imm & 0xFFFFF) << 12
    return imm20 | ((rd & 0x1F) << 7) | opcode

def encode_j_type(mnemonic, rd, imm):
    info = J_TYPE[mnemonic]
    # FIX: Handle 21-bit 2's complement for negative jump offsets
    # (imm is 21 bits, but bit 0 is always 0 and not encoded)
    imm21 = imm & 0x1FFFFF if imm >= 0 else (imm + (1 << 21)) & 0x1FFFFF
    
    imm20 = (imm21 >> 20) & 0x1      # bit 20
    imm10_1 = (imm21 >> 1) & 0x3FF   # bits 10:1
    imm11 = (imm21 >> 11) & 0x1    # bit 11
    imm19_12 = (imm21 >> 12) & 0xFF  # bits 19:12
    
    return (imm20 << 31) | (imm10_1 << 21) | (imm11 << 20) | (imm19_12 << 12) | \
        ((rd & 0x1F) << 7) | (info['opcode'] & 0x7F)

# === Utility functions ===

def prompt_for_path(prompt_msg, must_exist=False, default=None):
    """
    Prompt user for a file path. If must_exist=True, keep prompting until an existing file path is entered.
    If must_exist=False, check that directory exists.
    default: default path to show in prompt.
    """
    while True:
        if default:
            resp = input(f"{prompt_msg} [default: {default}]: ").strip()
            path = resp if resp else default
        else:
            path = input(f"{prompt_msg}: ").strip()
        # Strip quotes if any (from user input)
        if (path.startswith('"') and path.endswith('"')) or (path.startswith("'") and path.endswith("'")):
            path = path[1:-1]
        path = os.path.expanduser(path)
        if must_exist:
            if os.path.isfile(path):
                return path
            else:
                print(f"Path '{path}' does not exist or is not a file. Please try again.")
        else:
            dirn = os.path.dirname(path) or '.'
            if os.path.isdir(dirn):
                return path
            else:
                print(f"Directory '{dirn}' does not exist. Please enter a valid path.")

def write_verilog_memory_file(output_path, machine_words):
    """
    Write lines like:
        memory[0] = 32'hXXXXXXXX;
        memory[1] = 32'hYYYYYYYY;
    """
    try:
        with open(output_path, 'w') as f:
            for i, word in enumerate(machine_words):
                hexstr = f"{word & 0xFFFFFFFF:08X}"
                f.write(f"    memory[{i}] = 32'h{hexstr};\n")
    except Exception as e:
        print(f"Failed to write Verilog memory file '{output_path}': {e}", file=sys.stderr)
        sys.exit(1)
    print(f"Wrote Verilog memory assignments to '{output_path}', {len(machine_words)} entries.")

def write_hex_file(output_path, machine_words):
    """
    Write a v2.0 raw .hex file with header:
      v2.0 raw
    followed by each 32-bit machine word as 8 hex digits per line.
    """
    try:
        with open(output_path, 'w') as f:
            f.write("v2.0 raw\n")
            for word in machine_words:
                # Uppercase 8-digit hex without prefix
                f.write(f"{word & 0xFFFFFFFF:08X}\n")
    except Exception as e:
        print(f"Failed to write HEX file '{output_path}': {e}", file=sys.stderr)
        sys.exit(1)
    print(f"Wrote HEX file '{output_path}', {len(machine_words)} entries.")

# === Assembler logic ===

def updated_assemble(asm_lines):
    """
    First pass: collect labels and instruction lines.
    Second pass: encode each instruction to 32-bit word.
    """
    labels = {}
    instructions = []
    pc = 0
    # First pass: label collection
    for lineno, line in enumerate(asm_lines, start=1):
        # Remove comments
        if '#' in line:
            line = line.split('#', 1)[0]
        line = line.strip()
        if not line:
            continue
        # Check for label definition: label: possibly followed by instruction
        if ':' in line:
            parts = line.split(':', 1)
            label = parts[0].strip()
            if not re.match(r'^[A-Za-z_]\w*$', label):
                raise ValueError(f"Invalid label '{label}' on line {lineno}")
            if label in labels:
                raise ValueError(f"Duplicate label '{label}' on line {lineno}")
            labels[label] = pc
            rest = parts[1].strip()
            if rest:
                # There's instruction after label on same line
                instructions.append((lineno, rest))
                pc += 4
        else:
            instructions.append((lineno, line))
            pc += 4

    # Second pass: encode instructions
    machine_words = []
    for idx, (lineno, inst_line) in enumerate(instructions):
        curr_pc = idx * 4
        text = inst_line.strip()
        if not text:
            continue
        # Split tokens by whitespace, commas, parentheses.
        tokens = re.split(r'[,\s()]+', text)
        tokens = [tok for tok in tokens if tok]
        mnemonic = tokens[0].lower()
        try:
            if mnemonic in R_TYPE:
                # Expect: mnemonic rd, rs1, rs2
                if len(tokens) != 4:
                    raise ValueError(f"R-type '{mnemonic}' expects 3 operands (rd, rs1, rs2)")
                rd = parse_register(tokens[1])
                rs1 = parse_register(tokens[2])
                rs2 = parse_register(tokens[3])
                word = encode_r_type(mnemonic, rd, rs1, rs2)

            elif mnemonic in I_TYPE:
                # FIX: 'jalr' uses the same 'imm(rs1)' syntax as 'lw'
                if mnemonic == 'lw' or mnemonic == 'jalr':
                    # Expect: lw rd, imm(rs1) or jalr rd, imm(rs1)
                    # After split: tokens[1]=rd, tokens[2]=imm, tokens[3]=rs1
                    if len(tokens) != 4:
                        raise ValueError(f"Invalid {mnemonic} syntax on line {lineno}: '{inst_line}'. Expected '{mnemonic} rd, imm(rs1)'")
                    rd = parse_register(tokens[1])
                    imm = parse_immediate(tokens[2])
                    rs1 = parse_register(tokens[3])
                    word = encode_i_type(mnemonic, rd, rs1, imm)
                elif mnemonic in ('slli', 'srli', 'srai'):
                    # Expect: mnemonic rd, rs1, shamt
                    if len(tokens) != 4:
                        raise ValueError(f"Shift-immediate '{mnemonic}' expects 3 operands")
                    rd = parse_register(tokens[1])
                    rs1 = parse_register(tokens[2])
                    shamt = parse_immediate(tokens[3])
                    # Optionally: check shamt fits 5 bits (0..31)
                    if shamt < 0 or shamt > 31:
                        raise ValueError(f"Shift amount out of range 0..31: {shamt}")
                    word = encode_i_shift_type(mnemonic, rd, rs1, shamt)
                # FIX: Removed separate 'jalr' block which had wrong syntax
                else:
                    # Other I-type arithmetic: addi, andi, ori, xori, slti, sltiu
                    if len(tokens) != 4:
                        raise ValueError(f"I-type '{mnemonic}' expects 3 operands (rd, rs1, imm)")
                    rd = parse_register(tokens[1])
                    rs1 = parse_register(tokens[2])
                    imm = parse_immediate(tokens[3])
                    word = encode_i_type(mnemonic, rd, rs1, imm)

            elif mnemonic in S_TYPE:
                # sw rs2, imm(rs1)
                # After split: tokens = ['sw', 'rs2', 'imm', 'rs1']
                if len(tokens) != 4:
                    raise ValueError(f"S-type '{mnemonic}' expects syntax 'sw rs2, imm(rs1)'")
                rs2 = parse_register(tokens[1])
                imm = parse_immediate(tokens[2])
                rs1 = parse_register(tokens[3])
                word = encode_s_type('sw', rs2, rs1, imm)

            elif mnemonic in B_TYPE:
                # beq rs1, rs2, label_or_imm
                if len(tokens) != 4:
                    raise ValueError(f"B-type '{mnemonic}' expects 3 operands (rs1, rs2, target)")
                rs1 = parse_register(tokens[1])
                rs2 = parse_register(tokens[2])
                target = tokens[3]
                if re.match(r'^[A-Za-z_]\w*$', target):
                    if target not in labels:
                        raise ValueError(f"Undefined label '{target}' on line {lineno}")
                    target_addr = labels[target]
                    imm = target_addr - curr_pc
                else:
                    imm = parse_immediate(target)
                word = encode_b_type(mnemonic, rs1, rs2, imm)

            elif mnemonic in U_TYPE:
                # lui rd, imm  or auipc rd, imm
                if len(tokens) != 3:
                    raise ValueError(f"U-type '{mnemonic}' expects 2 operands (rd, imm20)")
                rd = parse_register(tokens[1])
                imm = parse_immediate(tokens[2])
                word = encode_u_type(mnemonic, rd, imm)

            elif mnemonic in J_TYPE:
                # jal rd, label_or_imm
                if len(tokens) != 3:
                    raise ValueError(f"J-type '{mnemonic}' expects 2 operands (rd, target)")
                rd = parse_register(tokens[1])
                target = tokens[2]
                if re.match(r'^[A-Za-z_]\w*$', target):
                    if target not in labels:
                        raise ValueError(f"Undefined label '{target}' on line {lineno}")
                    target_addr = labels[target]
                    imm = target_addr - curr_pc
                else:
                    imm = parse_immediate(target)
                word = encode_j_type('jal', rd, imm)

            else:
                raise ValueError(f"Unsupported instruction '{mnemonic}' on line {lineno}")

        except ValueError as ve:
            print(f"Error at line {lineno}: {ve}", file=sys.stderr)
            print(f"  >>> {inst_line}", file=sys.stderr)
            sys.exit(1)

        machine_words.append(word)

    return machine_words

def main():
    parser = argparse.ArgumentParser(description="Extended RISC-V RV32I assembler → Verilog memory[...] assignments and optional v2.0 raw .hex")
    parser.add_argument("--input", "-i", help="Input assembly file (.asm)")
    parser.add_argument("--output", "-o", help="Output file for Verilog assignments (.v)")
    parser.add_argument("--hex-output", "-x", help="Output file for v2.0 raw .hex (optional)")
    args = parser.parse_args()

    # Determine input path
    asm_path = None
    # 1. HARDCODE_INPUT_PATH if valid file
    if HARDCODE_INPUT_PATH:
        # FIX: Don't strip quotes from hardcoded variable
        p = os.path.expanduser(HARDCODE_INPUT_PATH)
        if os.path.isfile(p):
            asm_path = p
        else:
            # warn but continue
            print(f"Warning: HARDCODE_INPUT_PATH '{p}' not found. Ignoring hardcode.", file=sys.stderr)
    # 2. CLI arg
    if asm_path is None and args.input:
        p = os.path.expanduser(args.input.strip('"').strip("'"))
        if os.path.isfile(p):
            asm_path = p
        else:
            print(f"Warning: input file '{p}' not found. Will prompt.", file=sys.stderr)
    # 3. Prompt
    if asm_path is None:
        asm_path = prompt_for_path("Enter path to input .asm file", must_exist=True)

    # Determine output path (Verilog)
    out_path = None
    # 1. HARDCODE_OUTPUT_PATH if its directory exists
    if HARDCODE_OUTPUT_PATH:
        # FIX: Don't strip quotes from hardcoded variable
        p = os.path.expanduser(HARDCODE_OUTPUT_PATH)
        dirn = os.path.dirname(p) or '.'
        if os.path.isdir(dirn):
            out_path = p
        else:
            print(f"Warning: HARDCODE_OUTPUT_PATH directory '{dirn}' not exist. Ignoring hardcode.", file=sys.stderr)
    # 2. CLI arg
    if out_path is None and args.output:
        p = os.path.expanduser(args.output.strip('"').strip("'"))
        dirn = os.path.dirname(p) or '.'
        if os.path.isdir(dirn):
            out_path = p
        else:
            print(f"Warning: directory for output '{dirn}' does not exist. Will prompt.", file=sys.stderr)
    # 3. Prompt if still None
    if out_path is None:
        default_out = os.path.splitext(asm_path)[0] + "_mem.v"
        out_path = prompt_for_path("Enter path to output Verilog memory file", must_exist=False, default=default_out)

    # Determine hex output path
    hex_out_path = None
    # 1. HARDCODE_HEX_PATH if valid directory
    if HARDCODE_HEX_PATH:
        # FIX: Don't strip quotes from hardcoded variable
        p = os.path.expanduser(HARDCODE_HEX_PATH)
        dirn = os.path.dirname(p) or '.'
        if os.path.isdir(dirn):
            hex_out_path = p
        else:
            print(f"Warning: HARDCODE_HEX_PATH directory '{dirn}' not exist. Ignoring hardcode.", file=sys.stderr)
    # 2. CLI arg
    if hex_out_path is None and args.hex_output:
        p = os.path.expanduser(args.hex_output.strip('"').strip("'"))
        dirn = os.path.dirname(p) or '.'
        if os.path.isdir(dirn):
            hex_out_path = p
        else:
            print(f"Warning: directory for hex output '{dirn}' does not exist. Will prompt.", file=sys.stderr)
    # 3. Default derived from asm path if not provided (no prompt because hex is optional)
    if hex_out_path is None and args.hex_output is None:
        # default = <asm_basename>_mem.hex (in same directory)
        hex_out_path = os.path.splitext(out_path)[0] + ".hex"

    # Read lines
    try:
        with open(asm_path, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading '{asm_path}': {e}", file=sys.stderr)
        sys.exit(1)

    # Assemble
    try:
        machine_words = updated_assemble(lines)
    except Exception as e:
        print(f"Assembly failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Write outputs
    write_verilog_memory_file(out_path, machine_words)

    # If user explicitly passed --hex-output or default hex path computed, always write hex file.
    if hex_out_path:
        write_hex_file(hex_out_path, machine_words)

if __name__ == "__main__":
    main()