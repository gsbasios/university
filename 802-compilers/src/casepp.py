#!/usr/bin/env python3

# CASE++ Compiler - Version 3.0 | Lex/Syntax Analyzer, Intermediate Code, Symbol Table and Final Code

# ---------------------------------------------------------------------------------------------

import os
import sys
import difflib
import argparse
from enum import Enum

try:
    from colorama import Fore, init
    COLORAMA_INSTALLED = True
except ImportError:
    COLORAMA_INSTALLED = False 

# ---------------------------------- GLOBAL VARIABLES ------------------------------------------

OCCUPIED_WORDS = [
                    'program', 'declare', 'and', 'or', 'not', 'if', 'else', 'while', 
                    'switchcase', 'when', 'default', 'whilecase', 'incase', 'untilcase', 
                    'until', 'forcase', 'return', 'print', 'input', 'function', 'in', 'inout'
                 ]

LINES = []                  # a list with the lines of the whole program, used to report errors
TOKENS = []                 # list with the tokens
token = None                # the current token 
T_COUNTER = 0               # counter of temp variables T_i
VAR_LIST = []               # list with all the temp variables
QUAD_LIST = []              # list with all the quads
FILENAME = None             # the base name of the .c++ file
QUAD_COUNTER = 1            # counter of each quad
CURRENT_TOKEN_INDEX = 0     # index inside TOKENS list, used to store and get token

# ------------------------------------ BASIC CLASSES ---------------------------------------------

class NoColor:
    def __getattribute__(self, name):
        return ""

class Token:
    def __init__(self, category, token, line_counter, line_pos):
        self.category = category
        self.token = token
        self.line_counter = line_counter
        self.line_pos = line_pos

    def __str__(self):
        return f"{Fore.CYAN}{self.token:<30}{Fore.RESET} {Fore.LIGHTMAGENTA_EX}{self.category:<15}{Fore.RESET}{Fore.LIGHTYELLOW_EX}line {self.line_counter}"
    
class Error(Enum):
    SYNTAX = "SYNTAX ERROR"
    ILLEGAL_SYMBOL = "ILLEGAL SYMBOL"
    ILLEGAL_INT = "ILLEGAL INTEGER"

# ---------------------------- HELPER METHODS ------------------------------------------------

def report_error(error, message, line, line_number, line_pos):
    error = error.value
    
    offset = len(line) - len(line.lstrip())
    line = line.lstrip()
    line_pos = line_pos - offset
    
    error_dist = len(f"{error}") + 2
    line_dist = len(f"in line {line_number}")
    maxdist = max(error_dist, line_dist)
    mindist = min(error_dist, line_dist)
    
    print(f"{Fore.RED}{error}: {Fore.RED}{message}")
    print(f"{Fore.LIGHTYELLOW_EX}in line {line_number} {' '*(maxdist -1- mindist)}{line}")
    print(f"{' '*(line_pos+maxdist-1)}{Fore.RED}^")
    
    sys.exit(1)
    

def is_valid_integer(value):
    try:
        integer = int(value)
        if integer >= -32767 and integer <= 32767: return True
        else: return False
    except ValueError:
        return False
    
    
def check_extension(infile):
    global FILENAME
    ext = infile.rsplit('.', 1)[1]
    FILENAME = infile.rsplit('.', 1)[0]
    if ext != 'c++':
        print(f"{Fore.RED}ERROR:{Fore.RESET} Invalid file extension: {Fore.YELLOW}.{ext}{Fore.RESET} (Did you mean .c++?)")
        sys.exit(1)
        
        
def get_token():
    global CURRENT_TOKEN_INDEX
    
    if CURRENT_TOKEN_INDEX >= len(TOKENS): return Token("EOF", "EOF", 0, 0)
    else:
        token = TOKENS[CURRENT_TOKEN_INDEX]
        CURRENT_TOKEN_INDEX += 1
        return token

    
def store_token():
    global CURRENT_TOKEN_INDEX
    
    if CURRENT_TOKEN_INDEX >= len(TOKENS): return Token("EOF", "EOF", 0, 0)
    else: return TOKENS[CURRENT_TOKEN_INDEX]


def word_prediction(word, possibilities):
    word = str(word)
    matches = difflib.get_close_matches(word, possibilities, n=1, cutoff=0.75)
    return matches[0] if matches else None


def get_line_pos(token):
    if token: return token.line_pos
    else: return 0
    
    
def initialize_lines(infile):
    global LINES
    
    raw = infile.read().splitlines()
    LINES.append("")
    for line in raw:
        l = line.split("//")[0] # REMOVE THE COMMENTS FROM THE ERROR REPORTING
        LINES.append(l)
            
    LINES.append("")
    infile.seek(0)
    
    
def initialize_colors(args_color):
    if COLORAMA_INSTALLED and not args_color:
        init(autoreset=True)
    else:
        global Fore
        Fore = NoColor()
        
# ---------------------------- INTERMEDIATE CODE FUNCTIONS AND CLASS ------------------------------------------------
class Quad:
    def __init__(self, label, op, x, y, z):
        self.label = str(label)
        self.op = str(op)
        self.x = str(x)
        self.y = str(y)
        self.z = str(z)
        
    def __str__(self):
        pad = 1
        if QUAD_LIST:
            max_num = QUAD_LIST[-1].label
            pad = len(max_num)
            
        return f"{self.label:<{pad}}: {self.op}, {self.x}, {self.y}, {self.z}"

def newTemp():
    global T_COUNTER, VAR_LIST
    T_COUNTER += 1
    temp = "T_" + str(T_COUNTER)
    VAR_LIST.append(temp)
    offset = sym_table.get_current_offset()
    sym_table.insert_entity(TempVar(temp, offset, "INT"))
    sym_table.update_offset()
    return temp
    
def nextQuad():
    return QUAD_COUNTER

def genQuad(op, x, y, z):
    global QUAD_COUNTER, QUAD_LIST
    QUAD_LIST.append(Quad(nextQuad(), op, x, y, z))
    QUAD_COUNTER += 1
    
def emptyList():
    return []

def makeList(label):
    return [label]

def mergeList(list1, list2):
    return list1 + list2

def backpatch(lst, label):
    global QUAD_LIST
    for i in lst:
        if QUAD_LIST[i-1].z != "_":
            print(f"{Fore.RED}ERROR: Quad {QUAD_LIST[i-1]} has issues!")
            sys.exit(1)
        QUAD_LIST[i-1].z = str(label)
        
def write_int_code(QUAD_LIST):
    outfile = f"{FILENAME}.int"
    
    with open(outfile, "w", encoding="utf-8") as f:
        for q in QUAD_LIST:
            f.write(f"{q}\n")
            
    full_path = os.path.abspath(outfile)
    print(f"{Fore.GREEN}Intermediate code saved to: {full_path}")
        

# ---------------------------- SYMBOL TABLE -----------------------------------------------

class Argument:
    def __init__(self, parMode, type="INT"):
        self.parMode = parMode  
        self.type = type    

class Entity:
    def __init__(self, name):
        self.name = name

class Variable(Entity):
    def __init__(self, name, offset, type="INT"):
        super().__init__(name)
        self.type = type
        self.offset = offset   

class Function(Entity):
    def __init__(self, name, type="INT"):
        super().__init__(name)
        self.type = type
        self.startQuad = None   
        self.argument_list = [] 
        self.framelength = None 

class Constant(Entity):
    def __init__(self, name, value):
        super().__init__(name)
        self.value = value      

class Parameter(Entity):
    def __init__(self, name, parMode, offset, type="INT"):
        super().__init__(name)
        self.type = type
        self.parMode = parMode  
        self.offset = offset    

class TempVar(Entity):
    def __init__(self, name, offset, type="INT"):
        super().__init__(name)
        self.type = type
        self.offset = offset   

class Scope:
    def __init__(self, nestingLevel):
        self.entity_list = []            
        self.nestingLevel = nestingLevel 
        self.offset = 12                 

    def add_entity(self, entity):
        self.entity_list.append(entity)

class SymbolTable:
    def __init__(self):
        self.scopes = []
        self.sym_buffer = "" 

    def add_scope(self):
        if not self.scopes:
            new_level = 0
        else:
            new_level = self.scopes[-1].nestingLevel + 1
        self.scopes.append(Scope(new_level))

    def remove_scope(self):
        self.print_scope()          
        self.buffer_scope()       
        self.scopes.pop()

    def insert_entity(self, entity):
        self.scopes[-1].add_entity(entity)
        
    def get_current_offset(self):
        return self.scopes[-1].offset
        
    def update_offset(self):
        self.scopes[-1].offset += 4

    def search_entity(self, name):
        for scope in reversed(self.scopes):
            for entity in scope.entity_list:
                if entity.name == name:
                    return entity, scope.nestingLevel
        return None, -1

    def print_scope(self):
        if not self.scopes: return
        scope = self.scopes[-1]
        print(f"\n{Fore.MAGENTA}--- SCOPE LEVEL {scope.nestingLevel} ---{Fore.RESET}")
        for ent in scope.entity_list:
            if isinstance(ent, Variable):
                print(f"  VAR: {ent.name}, offset: {ent.offset}")
            elif isinstance(ent, Parameter):
                print(f"  PAR: {ent.name}, mode: {ent.parMode}, offset: {ent.offset}")
            elif isinstance(ent, TempVar):
                print(f"  TMP: {ent.name}, offset: {ent.offset}")
            elif isinstance(ent, Function):
                print(f"  FUNC: {ent.name}, startQuad: {ent.startQuad}, frameLength: {ent.framelength}")

    def buffer_scope(self):
        if not self.scopes: return
        scope = self.scopes[-1]
        self.sym_buffer += f"\n--- SCOPE LEVEL {scope.nestingLevel} ---\n"
        for ent in scope.entity_list:
            if isinstance(ent, Variable):
                self.sym_buffer += f"  VAR: {ent.name}, offset: {ent.offset}\n"
            elif isinstance(ent, Parameter):
                self.sym_buffer += f"  PAR: {ent.name}, mode: {ent.parMode}, offset: {ent.offset}\n"
            elif isinstance(ent, TempVar):
                self.sym_buffer += f"  TMP: {ent.name}, offset: {ent.offset}\n"
            elif isinstance(ent, Function):
                self.sym_buffer += f"  FUNC: {ent.name}, startQuad: {ent.startQuad}, frameLength: {ent.framelength}\n"
        self.sym_buffer += "-----------------------\n\n"

    def write_to_file(self):
        outfile = f"{FILENAME}.sym"
        with open(outfile, "w", encoding="utf-8") as f:
            f.write(self.sym_buffer)
        full_path = os.path.abspath(outfile)
        print(f"\n{Fore.GREEN}Symbol Table saved to: {full_path}")


sym_table = SymbolTable()

#----------------------------FINAL CODE ----------------------------------------------------
ASM_LIST = []

def genAsm(instruction):
    global ASM_LIST
    ASM_LIST.append(instruction)

def gnvlcode(v):
    entity, entity_level = sym_table.search_entity(v)
    current_level = sym_table.scopes[-1].nestingLevel
    
    genAsm("\tlw t0, -4(sp)")
    levels_up = current_level - entity_level
    for _ in range(levels_up - 1):
        genAsm("\tlw t0, -4(t0)")
        
    genAsm(f"\taddi t0, t0, -{entity.offset}")
    
def loadvr(v, r):
    if str(v).isdigit() or (str(v).startswith('-') and str(v)[1:].isdigit()):
        genAsm(f"\tli {r}, {v}")
        return
        
    entity, level = sym_table.search_entity(v)
    current_level = sym_table.scopes[-1].nestingLevel
    
    if level == 0:
        genAsm(f"\tlw {r}, -{entity.offset}(gp)")
    elif level == current_level:
        if isinstance(entity, Variable) or isinstance(entity, TempVar) or (isinstance(entity, Parameter) and entity.parMode == 'CV'):
            genAsm(f"\tlw {r}, -{entity.offset}(sp)")
        elif isinstance(entity, Parameter) and entity.parMode == 'REF':
            genAsm(f"\tlw t0, -{entity.offset}(sp)")
            genAsm(f"\tlw {r}, 0(t0)")
    elif level < current_level:
        if isinstance(entity, Variable) or (isinstance(entity, Parameter) and entity.parMode == 'CV'):
            gnvlcode(v)
            genAsm(f"\tlw {r}, 0(t0)")
        elif isinstance(entity, Parameter) and entity.parMode == 'REF':
            gnvlcode(v)
            genAsm("\tlw t0, 0(t0)")
            genAsm(f"\tlw {r}, 0(t0)")

def storerv(r, v):
    entity, level = sym_table.search_entity(v)
    current_level = sym_table.scopes[-1].nestingLevel
    
    if level == 0:
        genAsm(f"\tsw {r}, -{entity.offset}(gp)")
    elif level == current_level:
        if isinstance(entity, Variable) or isinstance(entity, TempVar) or (isinstance(entity, Parameter) and entity.parMode == 'CV'):
            genAsm(f"\tsw {r}, -{entity.offset}(sp)")
        elif isinstance(entity, Parameter) and entity.parMode == 'REF':
            genAsm(f"\tlw t0, -{entity.offset}(sp)")
            genAsm(f"\tsw {r}, 0(t0)")
    elif level < current_level:
        if isinstance(entity, Variable) or (isinstance(entity, Parameter) and entity.parMode == 'CV'):
            gnvlcode(v)
            genAsm(f"\tsw {r}, 0(t0)")
        elif isinstance(entity, Parameter) and entity.parMode == 'REF':
            gnvlcode(v)
            genAsm("\tlw t0, 0(t0)")
            genAsm(f"\tsw {r}, 0(t0)")

def generate_assembly(start_q, end_q, block_name):
    global ASM_LIST
    
    block_entity, caller_level = sym_table.search_entity(block_name)
    
    if block_entity is None:
        is_main = True
        framelength = sym_table.get_current_offset()
        caller_level = 0
    else:
        is_main = False
        framelength = block_entity.framelength
    
    param_count = 0 
    
    for i in range(start_q - 1, end_q):
        q = QUAD_LIST[i]
        op, x, y, z = q.op, q.x, q.y, q.z
        
        genAsm(f"L{q.label}:")
        
        if op == "jump":
            genAsm(f"\tb L{z}")
            
        elif op in ["=", "<", ">", "<=", ">=", "<>"]:
            loadvr(x, "t1")
            loadvr(y, "t2")
            branch_instr = {"=": "beq", "<": "blt", ">": "bgt", "<=": "ble", ">=": "bge", "<>": "bne"}[op]
            genAsm(f"\t{branch_instr} t1, t2, L{z}")
            
        elif op == ":=":
            loadvr(x, "t1")
            storerv("t1", z)
            
        elif op in ["+", "-", "*", "/"]:
            loadvr(x, "t1")
            loadvr(y, "t2")
            asm_op = {"+": "add", "-": "sub", "*": "mul", "/": "div"}[op]
            genAsm(f"\t{asm_op} t1, t1, t2")
            storerv("t1", z)
            
        elif op == "out":
            loadvr(x, "a0")
            genAsm("\tli a7, 1")
            genAsm("\tecall")
            genAsm("\tla a0, str_nl")
            genAsm("\tli a7, 4")
            genAsm("\tecall")
            
        elif op == "inp":
            genAsm("\tli a7, 5")
            genAsm("\tecall")
            storerv("a0", x)
            
        elif op == "retv":
            loadvr(x, "t1")
            genAsm("\tlw t0, -8(sp)")
            genAsm("\tsw t1, 0(t0)")
            
        elif op == "par":
            if param_count == 0:
                genAsm(f"\taddi fp, sp, {framelength}") 
                
            if y == "CV":
                loadvr(x, "t0")
                genAsm(f"\tsw t0, -{12 + 4 * param_count}(fp)")
                param_count += 1
                
            elif y == "RET":
                entity, _ = sym_table.search_entity(x)
                genAsm(f"\taddi t0, sp, -{entity.offset}")
                genAsm(f"\tsw t0, -8(fp)")
                
            elif y == "REF":
                entity, entity_level = sym_table.search_entity(x)
                
                if entity_level == caller_level:
                    if isinstance(entity, Variable) or isinstance(entity, TempVar) or (isinstance(entity, Parameter) and entity.parMode == 'CV'):
                        genAsm(f"\taddi t0, sp, -{entity.offset}")
                        genAsm(f"\tsw t0, -{12 + 4 * param_count}(fp)")
                    elif isinstance(entity, Parameter) and entity.parMode == 'REF':
                        genAsm(f"\tlw t0, -{entity.offset}(sp)")
                        genAsm(f"\tsw t0, -{12 + 4 * param_count}(fp)")
                else:
                    if isinstance(entity, Variable) or (isinstance(entity, Parameter) and entity.parMode == 'CV'):
                        gnvlcode(x)
                        genAsm(f"\tsw t0, -{12 + 4 * param_count}(fp)")
                    elif isinstance(entity, Parameter) and entity.parMode == 'REF':
                        gnvlcode(x)
                        genAsm(f"\tlw t0, 0(t0)")
                        genAsm(f"\tsw t0, -{12 + 4 * param_count}(fp)")
                param_count += 1
                
        elif op == "call":
            func_ent, func_level = sym_table.search_entity(x)
            
            if caller_level == func_level:
                genAsm("\tlw t0, -4(sp)")
                genAsm("\tsw t0, -4(fp)")
            else:
                genAsm("\tsw sp, -4(fp)")
                
            genAsm(f"\taddi sp, sp, {framelength}")
            genAsm(f"\tjal L{func_ent.startQuad}")
            genAsm(f"\taddi sp, sp, -{framelength}") 
            
            param_count = 0 
            
        elif op == "begin_block":
            if is_main:
                genAsm(f"\taddi sp, sp, {framelength}") 
                genAsm("\tmv gp, sp")
            else:
                genAsm("\tsw ra, 0(sp)")
                
        elif op == "end_block":
            if not is_main:
                genAsm("\tlw ra, 0(sp)")
                genAsm("\tjr ra")
        elif op == "halt":
            genAsm("\tli a0, 0")
            genAsm("\tli a7, 93")
            genAsm("\tecall")

def write_asm_code():
    outfile = f"{FILENAME}.asm"
    
    main_start = 1
    for i in range(len(QUAD_LIST) - 1, -1, -1):
        if QUAD_LIST[i].op == "begin_block":
            main_start = QUAD_LIST[i].label
            break
            
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(".data\n")
        f.write("str_nl: .asciz \"\\n\"\n\n")
        f.write(".text\n")
        
        f.write(f"j L{main_start}\n\n")
        
        for instr in ASM_LIST:
            f.write(instr + "\n")
            
    full_path = os.path.abspath(outfile)
    print(f"{Fore.GREEN}RISC-V Assembly code saved to: {full_path}")

# ---------------------------- LEX ANALYZER ------------------------------------------------

def lex_analyzer(infile):
    global TOKENS
    line_counter = 1
    word_counter = 0
    token = ""
    line = ""
    char = infile.read(1)
    
    # IF char == "" WE REACHED THE END OF FILE
    while char != "": 
         
        # CHECK SPACES AND NEW LINES
        if char.isspace():
            if char == "\n": 
                line_counter +=1
                line = ""
                word_counter = 0
            else:   
                word_counter += 1
                line += char
            char = infile.read(1)
            continue

        # CHECK INTEGERS
        elif char.isdigit():
            token = ""
            # CREATE THE INTEGER
            while char.isdigit():
                token += char
                line += char
                word_counter += 1
                char = infile.read(1)
            
            # THROW ERROR IF ALPHABETICAL CHARACTER COMES UP
            if char.isalpha():
                line += char
                word_counter += 1
                report_error(Error.SYNTAX, "IDENTIFIERS starting with Integer cannot contain Alphabetic characters!", line, line_counter, word_counter)
                char = infile.read(1)
            # ELSE PUT THE INTEGER IN THE TOKENS, IF IT'S VALID
            else:
                if is_valid_integer(token):
                    TOKENS.append(Token("INTEGER", token, line_counter, word_counter))
                    token = ""
                    continue
                else:
                    report_error(Error.ILLEGAL_INT, "Integer is out of bounds!", line, line_counter, word_counter)
                    continue

        # CHECK ALPHANUMERICALS
        elif char.isalpha():
            token = ""
            while char.isalnum():
                token += char
                line += char
                char = infile.read(1)
                word_counter += 1

            # LIMIT TO 30 CHARACTERS
            if len(token) > 30:
                print(f"{Fore.YELLOW}WARNING: Variable '{Fore.CYAN}{token}{Fore.YELLOW}' in {Fore.CYAN}line {line_counter}{Fore.YELLOW} is bigger than 30 characters long")
                print(f"         {Fore.YELLOW}and will be trimmed to 30 as: {Fore.CYAN}{token[:30]}\n")
            token = token[:30]

            if token in OCCUPIED_WORDS:
                TOKENS.append(Token("KEYWORD", token, line_counter, word_counter))
                token = ""
            else:
                TOKENS.append(Token("IDENTIFIER", token, line_counter, word_counter))
                token = ""
            continue
            
        # CHECK MATH OPERATORS
        elif char in "+-*/=": 
            line += char
            word_counter += 1
            
            # CHECK IF IT'S MATH OP OR COMMENT
            if char == "/":
                next_char = infile.read(1)
                
                # IF BLOCK COMMENT STARTED
                if next_char == "*": 
                    line += next_char
                    word_counter += 1
                    comm_line = line_counter
                    prev_char = ""
                    
                    while True:
                        char = infile.read(1)
                        if char == "":
                            first_line = line.split("\n")[0]
                            report_error(Error.SYNTAX, "Unclosed comment!", first_line, comm_line, word_counter)
                            break
                            
                        line += char
                        word_counter += 1
                        
                        if char == "\n":
                            line_counter += 1
                            line = ""
                            word_counter = 0
                            prev_char = ""
                            
                        elif char == "*" and prev_char == "/":
                            report_error(Error.SYNTAX, "Nested comments are not allowed!", line, line_counter, word_counter)
                            
                        elif char == "/" and prev_char == "*":
                            char = infile.read(1)
                            break
                        else:
                            prev_char = char
                    continue
                
                # IF LINE COMMENT STARTED
                elif next_char == "/":
                    line += next_char 
                    word_counter += 1
                    prev_char = ""
                    
                    while True:
                        char = infile.read(1)
                        if char == "" or char == "\n":
                            if char == "\n": 
                                line_counter += 1
                                line = ""
                                word_counter = 0
                            char = infile.read(1)
                            break
                            
                        line += char
                        word_counter += 1
                        
                        if char == "*" and prev_char == "/":
                            report_error(Error.SYNTAX, "Nested comments are not allowed!", line, line_counter, word_counter)
                        elif char == "/" and prev_char == "/":
                            report_error(Error.SYNTAX, "Nested comments are not allowed!", line, line_counter, word_counter)
                        else:
                            prev_char = char
                    continue
                
                # ELSE IT'S MATH OP
                else:
                    TOKENS.append(Token("MUL_OP", "/", line_counter, word_counter))
                    char = next_char
                    continue
    
            # ADD '+' OR '-' OR '*' OR '='
            if char == "*":
                TOKENS.append(Token("MUL_OP", char, line_counter, word_counter))
                char = infile.read(1)
                continue
            elif char in "+-":
                TOKENS.append(Token("ADD_OP", char, line_counter, word_counter))
                char = infile.read(1)
                continue
            else:
                TOKENS.append(Token("RELATIONAL_OP", char, line_counter, word_counter))
                char = infile.read(1)
                continue

        # CHECK '<' SYMBOL
        elif char == "<":
            line += char
            word_counter += 1
            
            char = infile.read(1)
            line += char
            word_counter += 1
            if char == "=":
                TOKENS.append(Token("RELATIONAL_OP", "<=", line_counter, word_counter))
                char = infile.read(1)
                continue
            elif char == ">":
                TOKENS.append(Token("RELATIONAL_OP", "<>", line_counter, word_counter))
                char = infile.read(1)
                continue
            else:
                TOKENS.append(Token("RELATIONAL_OP", "<", line_counter, word_counter))
                continue
           
        # CHECK '>' SYMBOL 
        elif char == ">":
            line += char
            word_counter += 1
            
            char = infile.read(1)
            line += char
            word_counter += 1
            if char == "=":
                TOKENS.append(Token("RELATIONAL_OP", ">=", line_counter, word_counter))
                char = infile.read(1)
                continue
            else:
                TOKENS.append(Token("RELATIONAL_OP", ">", line_counter, word_counter))
                continue
            
        # CHECK : SYMBOL  
        elif char == ":":
            line += char
            word_counter += 1
            
            next_char = infile.read(1)
            line += next_char
                
            if next_char == "=":
                TOKENS.append(Token("ASSIGN_OP", ":=", line_counter, word_counter))
                char = infile.read(1)
                word_counter += 1
                continue
            else:
                TOKENS.append(Token("COLON", ":", line_counter, word_counter))
                line = line[:-1]
                char = next_char
                continue

        elif char in "()[]{}":
            line += char
            word_counter += 1
            TOKENS.append(Token("GROUP_SYMBOL", char, line_counter, word_counter))
            char = infile.read(1)
            continue

        elif char in ",;":
            line += char
            word_counter += 1
            TOKENS.append(Token("DELIMITER", char, line_counter, word_counter))
            char = infile.read(1)
            continue

        else:
            line += char
            word_counter += 1
            report_error(Error.ILLEGAL_SYMBOL, f"Symbol '{char}' doesn't exist in case++", line, line_counter, word_counter)
            char = infile.read(1)
            continue
    
    if TOKENS: TOKENS.append(Token("EOF", "EOF", line_counter + 1, 1))
    return
    
# ---------------------------- SYNTAX ANALYZER ------------------------------------------------

def optional_sign():
    global token
    
    next_token = store_token()
    if next_token.token in "-+":
        token = get_token()    


def mul_oper():
    global token
    
    next_token = store_token()
    if next_token.token in "*/":
        token = get_token()


def add_oper():
    global token
    
    next_token = store_token()
    if next_token.token in "-+":
        token = get_token()


def relational_oper():
    global token
    
    next_token = store_token()
    if next_token.category == "RELATIONAL_OP":
        token = get_token()
        return token.token
        
    else:
        error = token
        line_pos = get_line_pos(error)
        report_error(Error.SYNTAX, f"Expected a Relational Operator after '{error.token}'!", LINES[error.line_counter], error.line_counter, line_pos)    


def actualparitem():
    global token
    
    next_token = store_token()
    
    if next_token.token == "in":
        token = get_token()             # STORES 'in'
        a = expression()                # STORE EXPRESSION RESULT TO VARIABLE FOLLOWING 'in'
        genQuad("par", a, "CV", "_")    # GENERATE 'CV' PARAMETER QUAD
        
    elif next_token.token == "inout":
        token = get_token()             # STORES 'inout'
        next_token = store_token()
        
        if next_token.category != "IDENTIFIER":
            error = next_token
            line_pos = get_line_pos(error)
            report_error(Error.SYNTAX, f"Expected an Identifier but got {error.category} '{error.token}' instead!", LINES[error.line_counter], error.line_counter, line_pos)
            
        else: 
            token = get_token()             # STORES THE 'ID'
            b = token.token                 # STORE EXPRESSION RESULT TO VARIABLE FOLLOWING 'inout'
            genQuad("par", b, "REF", "_")   # GENERATE 'REF' PARAMETER QUAD
    
    elif next_token.token == ')': return    # EMPTY ACTUALPARITEM
    
    else:
        error = next_token
        line_pos = get_line_pos(error)
        report_error(Error.SYNTAX, f"Expected Keywords 'in'/'inout' but got '{error.token}' instead!", LINES[error.line_counter], error.line_counter, line_pos)    


def actualparlist():
    global token
    
    actualparitem()
    next_token = store_token()      # SHOULD EITHER STORE ',' OR ')'
    
    while next_token.token == ",":
        token = get_token()         # CONSUME THE ','
        actualparitem()
        next_token = store_token()
        
    if next_token.token in ["in", "inout"]:
        error = next_token
        line_pos = get_line_pos(error)
        report_error(Error.SYNTAX, f"Missing comma ',' before '{next_token.token}'", LINES[error.line_counter], error.line_counter, line_pos)    


def actualpars():
    global token
    
    actualparlist()
    next_token = store_token()
    
    if next_token.token != ")":
        error = next_token
        line_pos = get_line_pos(token) + 1
        report_error(Error.SYNTAX, f"Expected parenthesis ')' but got '{error.token}' instead!", LINES[error.line_counter], error.line_counter, line_pos)    
    
    else: token = get_token()


def idtail():
    global token
    
    token = get_token()             # STORES 'ID'
    name = token.token              # STORE IDENTIFIER
    
    next_token = store_token()
    if next_token.token == "(":     # IF IT'S FUNCTION CALL
        token = get_token()         # STORES '('
        next_token = store_token()
        
        if next_token.token in ["in", "inout"]:
            actualpars()                        # ENTER actualpars() WITH TOKEN STORING THE '('
            w = newTemp()                       # CREATE TEMPORARY VAR
            genQuad("par", w, "RET", "_")       # STORE FUNCTION RESULT TO TEMP VAR
            genQuad("call", name, "_", "_")     # GENERATE FUNCTION CALL QUAD
            return w                            # RETURN FUNCTION RESULT
            
        elif next_token.token == ")":           # EMPTY PARAMETER LIST
            token = get_token()                 # CONSUME THE ')'
            w = newTemp()                       # CREATE TEMPORARY VAR
            genQuad("par", w, "RET", "_")       # STORE FUNCTION RESULT TO TEMP VAR
            genQuad("call", name, "_", "_")     # GENERATE FUNCTION CALL QUAD
            return w                            # RETURN FUNCTION RESULT
        
        else:
            error = next_token
            line_pos = get_line_pos(error) - 1
            report_error(Error.SYNTAX, f"Expected Keywords 'in'/'inout' for parameters, or you misssed an Operator before the parenthesis '('?", LINES[error.line_counter], error.line_counter, line_pos)    

    return name

def factor():
    global token
    
    last = token
    next_token = store_token()
    
    if next_token.category == "INTEGER":
        token = get_token()
        t1_place = token.token      # IF INTEGER, JUST RETURN IT 
        
    elif next_token.token == "(":
        token = get_token()
        t1_place = expression()     # STORE EXPRESSION RESULT
        next_token = store_token()
        
        if next_token.token == ")": token = get_token()
        
        else:
            error = next_token
            line_pos = get_line_pos(error) - 1
            report_error(Error.SYNTAX, f"Expected parenthesis ')' but got '{error.token}' instead!", LINES[error.line_counter], error.line_counter, line_pos)      
    
    elif next_token.category == "IDENTIFIER": 
        token = store_token()   # STORES 'ID' WITHOUT CONSUMING
        t1_place = idtail()     # STORE IDTAIL RESULT, FUNCTION RESULT OR AN IDENTIFIER
        
    else:
        error = last
        line_pos = get_line_pos(error)
        report_error(Error.SYNTAX, f"Expected Integer, Identifier, or an Expression after '{error.token}'!", LINES[error.line_counter], error.line_counter, line_pos)
           
    return t1_place


def term():
    global token
    
    t1_place = factor()                     # STORE T1 RESULT
    next_token = store_token()              # STORES THE NEXT TOKEN OF 'factor'
    
    while next_token.token in "*/":         # STORE OPERATOR ('*' OR '/')
        op = next_token.token
        token = next_token
        mul_oper()
        t2_place = factor()                 # STORE T2 RESULT
        w = newTemp()                       # CREATE TEMPORARY VAR
        genQuad(op, t1_place, t2_place, w)  # GENERATE TERM QUAD, STORE RESULT 
        t1_place = w                        # TO TEMPORARY VAR
        next_token = store_token()          # REPEAT IF MORE EXIST
    
    return t1_place


def expression():
    global token
    
    optional_sign()           
    t1_place = term()                       # STORE T1 RESULT
    
    next_token = store_token()
    while next_token.token in "-+":
        op = next_token.token               # STORE OPERATOR ('+' OR '-')
        token = next_token
        add_oper()              
        t2_place = term()                   # STORE T2 RESULT
        w = newTemp()                       # CREATE TEMPORARY VAR
        genQuad(op, t1_place, t2_place, w)  # GENERATE EXPRESSION QUAD, STORE RESULT 
        t1_place = w                        # TO TEMPORARY VAR
        next_token = store_token()          # REPEAT IF MORE EXIST

    return t1_place


def boolfactor():
    global token
    
    next_token = store_token()
    
    if next_token.token == "not":
        token = get_token()                         # STORES 'not'
        next_token = store_token()                  # SHOULD STORE '['
        
        if next_token.token == "[":
            token = get_token()                     # STORES '['
            
            false_list, true_list = condition()     # IF 'not' KEYWORD, INVERT RESULTS IN TRUE/FALSE LISTS
            next_token = store_token()
            
            if next_token.token == "]": token = get_token()
            else:
                error = store_token()
                line_pos = get_line_pos(error)
                report_error(Error.SYNTAX, f"Symbol ']' was expected but got '{error.token}' instead!", LINES[error.line_counter], error.line_counter, line_pos)     
            
        else:
            error = next_token
            line_pos = get_line_pos(error)
            report_error(Error.SYNTAX, f"Symbol '[' was expected but got '{error.token}' instead!", LINES[error.line_counter], error.line_counter, line_pos)    
        
    elif next_token.token == "[":
        token = get_token()                 # STORES '['
        
        true_list, false_list = condition() # IF NOT 'not', KEEP RESULTS AS IS
        next_token = store_token()
        
        if next_token.token == "]": token = get_token()
        else:
            error = next_token
            line_pos = get_line_pos(error)
            report_error(Error.SYNTAX, f"Symbol ']' was expected but got '{error.token}' instead!", LINES[error.line_counter], error.line_counter, line_pos)          
        
    else:
        e1_place = expression()     # STORE E1 RESULT
        op = relational_oper()      # STORE OPERATOR
        e2_place = expression()     # STORE E2 RESULT
        
        true_list = makeList(nextQuad())        # CREATE TRUE LIST
        genQuad(op, e1_place, e2_place, "_")    # GENERATE BOOLFACTOR QUAD
        
        false_list = makeList(nextQuad())       # CREATE FALSE LIST
        genQuad("jump", "_", "_", "_")          # GENERATE JUMP QUAD
                                                # WILL BACKPATCH LATER
    return true_list, false_list


def boolterm():
    global token
    
    true_list, false_list = boolfactor()                    # CREATE TRUE/FALSE LISTS
    
    next_token = store_token()
    while next_token.token == "and":
        backpatch(true_list, nextQuad())                    # BACKPATCH TRUE LIST
        
        token = next_token
        next_token = get_token() # STORES 'and'
        
        true_list2, false_list2 = boolfactor()              # CREATE SECOND BOOLTERM TRUE/FALSE LISTS
                                                            # IF THEY EXIST
        true_list = true_list2                              # BOTH BOOLFACTORS SHOULD BE TRUE
        false_list = mergeList(false_list, false_list2)     # MERGE FALSE LISTS
                                                            # IF ONE IS FALSE, THE RESULT IS FALSE AS WELL
        next_token = store_token()
    
    return true_list, false_list


def condition():
    global token
    
    true_list, false_list = boolterm()                  # CREATE TRUE/FALSE LISTS
    
    next_token = store_token()
    while next_token.token == "or":
        backpatch(false_list, nextQuad())               # BACKPATCH FALSE LIST
        
        token = next_token
        next_token = get_token()                        # STORE 'or'
        
        true_list2, false_list2 = boolterm()            # CREATE SECOND BOOLTERM TRUE/FALSE LISTS
                                                        # IF THEY EXIST
        true_list = mergeList(true_list, true_list2)    # MERGE ALL THE TRUE LISTS
        false_list = false_list2                        # IF SECOND IN FALSE, WE JUST CHECK THE FIRST

        next_token = store_token()  

    return true_list, false_list


def return_stat():
    global token
    
    token = get_token()                     # STORES 'return'
    e_place = expression()                  # STORE EXPRESSION RESULT
    genQuad("retv", e_place, "_", "_")      # GENERATE RETURN QUAD


def input_stat():
    global token
    
    token = get_token() # STORES 'input'
    next_token = store_token()
    
    if next_token.category == "IDENTIFIER":
        token = get_token()
        id_place = token.token                  # STORE IDENTIFIER
        genQuad("inp", id_place, "_", "_")      # GENERATE INPUT QUAD
        
    elif next_token.token == ";":
        error = token
        line_pos = get_line_pos(error)
        report_error(Error.SYNTAX, f"An Identifier was expected after '{error.token}'!", LINES[error.line_counter], error.line_counter, line_pos)


def print_stat():
    global token
    
    token = get_token()                 # STORES 'print'
    e_place = expression()              # STORE EXPRESSION RESULT TO E
    genQuad("out", e_place, "_", "_")   # GENERATE PRINT QUAD


def untilcase_stat():
    global token
    
    token = get_token()                 # STORES 'untilcase'
    
    previous_false_list = emptyList()
    when_success_list = emptyList()
    loop_start_quad = nextQuad()
    next_token = store_token()
    while next_token.token == "when":
        next_token = get_token()        # STORES 'when'
        token = next_token

        backpatch(previous_false_list, nextQuad())
        true_list, false_list = condition()
        
        next_token = store_token()
        if next_token.token == ":": token = get_token()
        else:
            error = next_token
            line_pos = get_line_pos(error)
            report_error(Error.SYNTAX, f"Symbol ':' was expected after '{error.token}'!", LINES[error.line_counter], error.line_counter, line_pos)

        backpatch(true_list, nextQuad())

        statements()
        when_success_list = mergeList(when_success_list, makeList(nextQuad()))
        genQuad("jump", "_", "_", "_")
        
        previous_false_list = false_list
        
        next_token = store_token()
        
    next_token = store_token()
    if next_token.token == "until":
        next_token = get_token()        # STORES 'until'
        token = next_token
        until_check_quad = nextQuad()
        backpatch(previous_false_list, until_check_quad)
        backpatch(when_success_list, until_check_quad)
        
        until_true_list, until_false_list = condition()
        
        backpatch(until_false_list, loop_start_quad)
        
        backpatch(until_true_list, nextQuad())
    else:
        error = next_token
        line_pos = get_line_pos(error)
        report_error(Error.SYNTAX, f"Keyword 'until' was expected to close untilcase after'{error.token}'!", LINES[error.line_counter], error.line_counter, line_pos)


def forcase_stat():
    global token
    
    token = get_token() # STORES 'forcase'
    next_token = store_token()
    
    if next_token.category == "IDENTIFIER":
        token = get_token() # STORES 'ID'
        id = token.token
        next_token = store_token()
        
        if next_token.token == "=":
            token = get_token() # STORES '='
            next_token = store_token()
            
            if next_token.category == "INTEGER":
                token = get_token() # STORES 'INTEGER'
                integer = token.token
                genQuad(":=", integer, "_", id)
            else:
                error = next_token
                line_pos = get_line_pos(error)
                report_error(Error.SYNTAX, f"Expected an Integer but got {error.category} '{error.token}' instead!", LINES[error.line_counter], error.line_counter, line_pos)    
        else:
            error = next_token
            line_pos = get_line_pos(error)
            report_error(Error.SYNTAX, f"Symbol '=' was expected but got '{error.token}' instead!", LINES[error.line_counter], error.line_counter, line_pos)
    else:
        error = next_token
        line_pos = get_line_pos(error)
        report_error(Error.SYNTAX, f"Expected an Identifier but got {error.category} '{error.token}' instead!", LINES[error.line_counter], error.line_counter, line_pos)
    
    restart_quad = nextQuad()
    
    next_token = store_token()
    while next_token.token == "when":
        next_token = get_token()
        token = next_token
        true_list, false_list = condition()
        backpatch(true_list, nextQuad())
        
        next_token = store_token()
        if next_token.token == ":": token = get_token()
        else:
            error = next_token
            line_pos = get_line_pos(error)
            report_error(Error.SYNTAX, f"Symbol ':' was expected after '{error.token}'!", LINES[error.line_counter], error.line_counter, line_pos)

        statements()
        
        genQuad("jump", "_", "_", restart_quad)
        backpatch(false_list, nextQuad())
        
        next_token = store_token()


def incase_stat():
    global token
    
    token = get_token() # STORES 'incase'
    
    flag = newTemp()
    restart_quad = nextQuad()
    genQuad(":=", "0", "_", flag)
    
    next_token = store_token()
    while next_token.token == "when":
        next_token = get_token()
        token = next_token

        true_list, false_list = condition()
        backpatch(true_list, nextQuad())
        
        next_token = store_token()
        if next_token.token == ":": token = get_token()
        else:
            error = next_token
            line_pos = get_line_pos(error)
            report_error(Error.SYNTAX, f"Symbol ':' was expected after '{error.token}'!", LINES[error.line_counter], error.line_counter, line_pos)

        statements()
        
        genQuad(":=", "1", "_", flag)
        backpatch(false_list, nextQuad())

        next_token = store_token()
        
    genQuad("=", flag, "1", restart_quad)


def whilecase_stat():
    global token
    
    token = get_token() # STORES 'whilecase'
    
    previous_false_list = emptyList()
    restart_quad = nextQuad()
    
    next_token = store_token()
    while next_token.token == "when":
        next_token = get_token() # STORES 'when'
        token = next_token
        
        backpatch(previous_false_list, nextQuad())
        true_list, false_list = condition()
        
        next_token = store_token()
        
        if next_token.token == ":": token = get_token()
        else:
            error = next_token
            line_pos = get_line_pos(error)
            report_error(Error.SYNTAX, f"Symbol ':' was expected after '{error.token}'!", LINES[error.line_counter], error.line_counter, line_pos)

        backpatch(true_list, nextQuad())
        
        statements()
        
        genQuad("jump", "_", "_", restart_quad)
        previous_false_list = false_list
        
        next_token = store_token()
        
    if next_token.token == "default":
        token = get_token() # STORES 'default'
        next_token = store_token()
        
        if next_token.token == ":": token = get_token()
        else:
            error = next_token
            line_pos = get_line_pos(error)
            report_error(Error.SYNTAX, f"Symbol ':' was expected but got '{error.token}' instead!", LINES[error.line_counter], error.line_counter, line_pos)
        
        backpatch(previous_false_list, nextQuad())
        statements()
        
    else:
        error = next_token
        line_pos = get_line_pos(error)
        report_error(Error.SYNTAX, f"Keyword 'default' was expected to close whilecase after'{error.token}'!", LINES[error.line_counter], error.line_counter, line_pos)        


def switchcase_stat():
    global token
    
    exit_list = emptyList()             # HOLDS QUADS THAT JUMP OUTSIDE SWITCHCASE
    previous_false_list = emptyList()   # STORES EACH STEP'S PREVIOUS FALSE LIST
    
    token = get_token() # STORES 'switchcase'
    next_token = store_token()
    
    while next_token.token == "when":
        next_token = get_token() # STORES 'when'
        token = next_token
        
        backpatch(previous_false_list, nextQuad())      # IF PREVIOUS CONDITION FAILED, JUMP HERE
        true_list, false_list = condition()             # STORE CONDITION'S RESULTS
        
        next_token = store_token()
        
        if next_token.token == ":": token = get_token()
        else:
            error = next_token
            line_pos = get_line_pos(error)
            report_error(Error.SYNTAX, f"Symbol ':' was expected after '{error.token}'!", LINES[error.line_counter], error.line_counter, line_pos)

        backpatch(true_list, nextQuad())            # IF TRUE CONDITION, JUMP HERE AND
        statements()                                # EXECUTE IT'S STATEMENTS
        
        e_quad = makeList(nextQuad())               # CREATE THE EXIT QUAD
        genQuad("jump", "_", "_", "_")              # AND GENERATE JUMP

        exit_list = mergeList(exit_list, e_quad)    # ADD THIS EXIT QUAD TO EXIT LIST
        previous_false_list = false_list            # MAKE THIS FALSE LIST THE PREVIOUS, FOR NEXT LOOP
        
        next_token = store_token()
        
    token = next_token
    next_token = store_token()
        
    if next_token.token == "default":
        token = get_token() # STORES 'default'
        next_token = store_token()
        
        if next_token.token == ":": token = get_token()
        else:
            error = next_token
            line_pos = get_line_pos(error)
            report_error(Error.SYNTAX, f"Symbol ':' was expected but got '{error.token}' instead!", LINES[error.line_counter], error.line_counter, line_pos)
        
        backpatch(previous_false_list, nextQuad())  # THE LAST FALSE CONDITION WILL JUMP HERE
        statements()                                # AND EXECUTE STATEMENTS OF DEFAULT
        
    else:
        error = next_token
        line_pos = get_line_pos(error)
        report_error(Error.SYNTAX, f"Keyword 'default' was expected to close switchcase after '{error.token}'!", LINES[error.line_counter], error.line_counter, line_pos)

    backpatch(exit_list, nextQuad())    # BACKPATCH EXIT LIST TO JUMP OUTSIDE SWITCHCASE


def while_stat():
    global token
    
    token = get_token() # STORES 'while'
    
    b_quad = nextQuad()                     # STORE STARTING LABEL
    true_list, false_list = condition()     # CREATE TRUE/FALSE LISTS
    backpatch(true_list, nextQuad())        # BACKPATCH TRUE LIST
    
    statements()
    
    genQuad("jump", "_", "_", b_quad)       # JUMP TO THE STARTING POSITION TO REEVALUATE
    backpatch(false_list, nextQuad())       # BACKPATCH FALSE LIST


def elsepart():
    global token
    
    token = get_token() # STORES 'else'
    statements()


def if_stat():
    global token
    
    token = get_token()                     # STORES 'if'
    
    true_list, false_list = condition()     # STORE TRUE/FALSE LISTS
    backpatch(true_list, nextQuad())        # BACKPATCH TRUE LIST
    
    statements()
    
    next_token = store_token()
    if next_token.token == "else":
        if_list = makeList(nextQuad())      # IF ELSEPART EXISTS
        genQuad("jump", "_", "_", "_")      # CREATE AND BACKPATCH THE FALSE LIST
        backpatch(false_list, nextQuad())
        
        elsepart()
        backpatch(if_list, nextQuad())      # BACKPATCH AFTER ELSEPART
    else:
        backpatch(false_list, nextQuad())   # IF NO ELSEPART EXISTS, JUST BACKPATCH THE FALSE LIST                                            


def assignment_stat():
    global token
    
    token = get_token() # STORES ID
    assign_var = token.token                        # STORE THE VAR WHERE RESULT WILL BE STORED
    ent, level = sym_table.search_entity(assign_var)
    if ent is None:
        report_error(Error.SYNTAX, f"Semantic Error: Variable '{assign_var}' was not declared!", LINES[token.line_counter], token.line_counter, token.line_pos)
    next_token = store_token()
    
    if next_token.token == ":=":
        token = get_token()
        e_place = expression()                      # STORE EXPRESSSION RESULT
        genQuad(":=", e_place, "_", assign_var)     # AND CREATE THE ASSIGNMENT QUAD
        
    else:
        error = token
        line_pos = get_line_pos(error)
        
        KEYWORDS = ["if", "else", "while", "switchcase", "whilecase", "incase", "forcase", "untilcase", "print", "input", "return", "declare", "function"]
        next = word_prediction(error.token, KEYWORDS)

        if next:
            report_error(Error.SYNTAX, f"Unexpected word '{error.token}' came up. Did you mean '{next}'?", LINES[error.line_counter], error.line_counter, line_pos)
        else:    
            report_error(Error.SYNTAX, f"Expected Symbol ':=' after '{error.token}' but got '{next_token.token}' instead!", LINES[error.line_counter], error.line_counter, line_pos)


def statement():
    global token
    
    next_token = store_token() # SHOULD STORE A STATEMENT KEYWORD
    
    if next_token.token == "if":
        token = next_token
        if_stat()
    
    elif next_token.token == "while":
        token = next_token
        while_stat()
    
    elif next_token.token == "switchcase":
        token = next_token
        switchcase_stat()
        
    elif next_token.token == "whilecase":
        token = next_token
        whilecase_stat()
        
    elif next_token.token == "incase":
        token = next_token
        incase_stat()
        
    elif next_token.token == "forcase":
        token = next_token
        forcase_stat()
        
    elif next_token.token == "untilcase":
        token = next_token
        untilcase_stat()
        
    elif next_token.token == "print":
        token = next_token
        print_stat()

    elif next_token.token == "input":
        input_stat()   
    
    elif next_token.token == "return":
        token = next_token
        return_stat()
        
    else:
        if next_token.category == "IDENTIFIER":
            token = next_token
            assignment_stat()
        
        elif next_token.category == "KEYWORD":
            error = next_token
            line_pos = get_line_pos(error)
            report_error(Error.SYNTAX, f"Unexpected Keyword '{error.token}' came up where a statement expected!", LINES[error.line_counter], error.line_counter, line_pos)           
        
        else:
            error = next_token
            line_pos = get_line_pos(error)
            report_error(Error.SYNTAX, f"Expected a statement but got '{error.token}'!", LINES[error.line_counter], error.line_counter, line_pos)    


def statements_sequence():
    global token
    
    next_token = store_token()
    if next_token.token == "}":
        return
    
    statement()

    next_token = store_token()
    while next_token.token == ";":
        next_token = get_token()
        token = next_token
        statement()
        next_token = store_token()
      
    token = next_token
    if token.token not in ["}", "EOF", "default", "until", "when", "else"]:
        error = token
        line_pos = get_line_pos(error) - len(error.token) + 1
        report_error(Error.SYNTAX, f"You missed ';' before '{error.token}'!", LINES[error.line_counter], error.line_counter, line_pos)


def statements():
    global token
    
    next_token = store_token()
    if next_token.token == "{":
        token = get_token() # CONSUME THE '{'
        statements_sequence()
        
        next_token = store_token()
        
        if next_token.token == "}":
            token = get_token()
            
        else:
            error = token
            line_pos = get_line_pos(error) - len(error.token) + 1
            report_error(Error.SYNTAX, f"Symbol '}}' was expected before '{error.token}'!", LINES[error.line_counter], error.line_counter, line_pos)    
    
    else: statement()


def formalparitem(func_entity):
    global token
    
    next_token = store_token()
    
    if next_token.token == "in" or next_token.token == "inout":
        mode = "CV" if next_token.token == "in" else "REF"
        token = get_token() # STORES 'in' OR 'inout'
        next_token = store_token()
        
        if next_token.category == "IDENTIFIER":
            token = get_token() # STORES 'ID'
            func_entity.argument_list.append(Argument(mode, "INT"))
            id_name = token.token
            offset = sym_table.get_current_offset()
            sym_table.insert_entity(Parameter(id_name, mode, offset, "INT"))
            sym_table.update_offset()
            
        else:
            error = next_token
            line_pos = get_line_pos(error)
            report_error(Error.SYNTAX, f"Expected an Identifier but got {error.category} '{error.token}' instead!", LINES[error.line_counter], error.line_counter, line_pos)
    
    # EMPTY FORMALPARITEMS
    elif next_token.token == ')': return    
    
    else:
        error = next_token
        line_pos = get_line_pos(error)
        report_error(Error.SYNTAX, f"Expected Keywords 'in'/'inout' but got '{error.token}' instead!", LINES[error.line_counter], error.line_counter, line_pos)    


def formalparlist(func_entity):
    global token
    
    token = store_token()
    
    # EMPTY LIST
    if token.token == ")": return
    
    formalparitem(func_entity)
    next_token = store_token()
        
    if next_token.token in ["in", "inout"]:
        error = next_token
        line_pos = get_line_pos(error)
        report_error(Error.SYNTAX, f"Missing comma ',' before '{error.token}'!", LINES[error.line_counter], error.line_counter, line_pos)
     
    # EXITS WHILE WITH STORED THE LAST ELEM BEFORE ')'       
    while next_token.token == ",":
        token = get_token()
        formalparitem(func_entity)
        next_token = store_token()
        
        if next_token.token in ["in", "inout"]:
            error = next_token
            line_pos = get_line_pos(error)
            report_error(Error.SYNTAX, f"Missing comma ',' before '{error.token}'!", LINES[error.line_counter], error.line_counter, line_pos)


def formalpars(func_entity):
    global token
    
    next_token = store_token() # SHOULD STORE '('
    
    if next_token.token == "(":
        token = get_token() # STORES '('
        formalparlist(func_entity)
        
        next_token = store_token()
        
        if next_token.token == ")": token = get_token()
        else:
            token = next_token
            line_pos = get_line_pos(token)
            report_error(Error.SYNTAX, f"Expected parenthesis ')' but got '{token.token}' instead!", LINES[token.line_counter], token.line_counter, line_pos)
    
    else:
        error = next_token
        line_pos = get_line_pos(error)
        report_error(Error.SYNTAX, f"Expected parenthesis '(' but got '{error.token}' instead!", LINES[error.line_counter], error.line_counter, line_pos)


def function():
    global token
    
    token = get_token() 
    
    next_token = store_token()
    if next_token.category == "IDENTIFIER":
        token = get_token() 
        func_name = token.token
        func_entity = Function(func_name, "INT")
        sym_table.insert_entity(func_entity)
        sym_table.add_scope()
        formalpars(func_entity)
        programblock(func_name, is_main=False, func_entity=func_entity)
        sym_table.remove_scope()
    else:
        error = next_token
        line_pos = get_line_pos(error)
        report_error(Error.SYNTAX, f"Expected an Identifier but got {error.category} '{error.token}' instead!", LINES[error.line_counter], error.line_counter, line_pos)


def functions():
    global token
        
    next_token = store_token()
    
    while next_token.token == "function":
        token = next_token
        function() # CALLS function() WITHOUT STORING 'function'
        next_token = store_token()


def varlist():
    global token
    
    next_token = store_token() # SHOULD STORE 'ID'
    
    if next_token.category == "IDENTIFIER":
        token = get_token() # STORES 'ID'
        offset=sym_table.get_current_offset()
        sym_table.insert_entity(Variable(token.token, offset, "INT"))
        sym_table.update_offset()
        
        next_token = store_token()
        if next_token.category == "IDENTIFIER":
            error = next_token
            line_pos = get_line_pos(error)
            report_error(Error.SYNTAX, f"Missing comma ',' before '{error.token}'!", LINES[error.line_counter], error.line_counter, line_pos)
            
        while store_token().token == ",":
            next_token = get_token()
            token = next_token
            
            next_token = store_token()
                
            if next_token.category == "IDENTIFIER": 
                token = get_token() # STORES ID
                offset = sym_table.get_current_offset()
                sym_table.insert_entity(Variable(token.token, offset, "INT"))
                sym_table.update_offset()
                next_token = store_token()
                
                if next_token.category == "IDENTIFIER":
                    error = next_token
                    line_pos = get_line_pos(error)
                    report_error(Error.SYNTAX, f"Missing comma ',' before '{error.token}'!", LINES[error.line_counter], error.line_counter, line_pos)
                    
            else:
                error = next_token
                line_pos = get_line_pos(error)
                report_error(Error.SYNTAX, f"Expected an Identifier but got {error.category} '{error.token}' instead!", LINES[error.line_counter], error.line_counter, line_pos)
        
    elif next_token.token == ";": return
    
    else:
        error = next_token
        line_pos = get_line_pos(error)
        report_error(Error.SYNTAX, f"Expected an Identifier but got {error.category} '{error.token}' instead!", LINES[error.line_counter], error.line_counter, line_pos)


def declarations():
    global token
    
    next_token = store_token()
    while next_token.token == "declare":
        next_token = get_token() # STORES 'declare'
        token = next_token
        varlist()

        next_token = store_token()
        if next_token.token == ";": token = get_token()
        else:
            error = next_token
            line_pos = get_line_pos(error)
            report_error(Error.SYNTAX, f"Missing ';' after '{error.token}'", LINES[error.line_counter], error.line_counter, line_pos)
        
        next_token = store_token() 


def programblock(name, is_main, func_entity=None):
    global token
    
    next_token = store_token()      # SHOULD STORE '{'
    if next_token.token == "{":
        token = get_token()         # STORES '{'
        declarations()              # CHECK DECLARATIONS
        functions()    
        start_q = nextQuad()
        if func_entity is not None:
            func_entity.startQuad = start_q  # CHECK FUNCTIONS
        genQuad("begin_block", name, "_", "_")      # GENERATE BLOCK BEGIN QUAD
        statements_sequence()
        if is_main:                                 # ONLY 'halt' IF MAIN PROGRAM CALLED
            genQuad("halt", "_", "_", "_")          # GENERATE HALT QUAD
        genQuad("end_block", name, "_", "_")        # GENERATE BLOCK END QUAD
        if func_entity is not None:
            func_entity.framelength = sym_table.get_current_offset()
        end_q = nextQuad() - 1
        generate_assembly(start_q, end_q, name)
        next_token = store_token()                  # SHOULD STORE '}'
        
        if next_token.token == "}": token = get_token()
        else:
            error = next_token
            line_pos = get_line_pos(error)
            report_error(Error.SYNTAX, f"Symbol '}}' was expected but got '{error.token}' instead!", LINES[error.line_counter], error.line_counter, line_pos)        

    else:
        error = next_token
        line_pos = get_line_pos(error)
        report_error(Error.SYNTAX, f"Symbol '{{' was expected but got '{error.token}' instead!", LINES[error.line_counter], error.line_counter, line_pos)        


def program():
    global token
    
    token = get_token()             
    if token.token == "program":
        
        next_token = store_token()                  
        if next_token.category == "IDENTIFIER":
            token = get_token()                     
            prog_name = token.token  
            sym_table.add_scope()
            programblock(prog_name, is_main=True)   
            sym_table.remove_scope()
            
        else:
            error = next_token
            line_pos = get_line_pos(error)
            report_error(Error.SYNTAX, f"Program name was expected but got {error.category} '{error.token}' instead! Only Identifier are acceptable!", LINES[error.line_counter], error.line_counter, line_pos)
    else:
        error = token
        line_pos = get_line_pos(error)
        report_error(Error.SYNTAX, f"Keyword 'program' was expected but got '{error.token}' instead!", LINES[error.line_counter], error.line_counter, line_pos)


def syntax_analyzer():
    global token
    global CURRENT_TOKEN_INDEX
    
    CURRENT_TOKEN_INDEX = 0

    program()
    
    if store_token().token != "EOF":
        error_token = store_token()
        report_error(Error.SYNTAX, "Unexpected tokens found after the end of the program!", LINES[-1], error_token.line_counter, error_token.line_pos)
    
# ---------------------------------------- MAIN ------------------------------------------------ 
def run_compiler(raw_infile, obj_infile, print_flag, color_flag):
    check_extension(raw_infile)

    initialize_lines(obj_infile)    # INITIALIZE THE LINES TO PRINT ERRORS
    initialize_colors(color_flag)   # INITIALIZE COLORING FEATURES
                
    lex_analyzer(obj_infile)        # RUN LEX_ANALYZER
            
    if print_flag:                  # PRINT TOKENS
        for t in TOKENS: 
            print(t)

    syntax_analyzer()               # RUN SYNTAX_ANALYZER

    #write_int_code(QUAD_LIST)       # WRITE INT CODE TO FILE
    sym_table.write_to_file()
    write_asm_code()
    
def main():
    parser = argparse.ArgumentParser(description="CASE++ Compiler: Turn your .c++ programs into executable (RISC-V ARCH)")
    parser.add_argument("-v", "--version", action="version", version="CASE++ Compiler 3.0 | Basios Georgios & Pappas Victor")
    parser.add_argument("infile", help="The filename of your .c++ program")
    parser.add_argument("--print-tokens", action="store_true", help="Print all the tokens that were saved from the lex analyzer")
    parser.add_argument("--no-color", action="store_true", help="Use this flag for colorless output")
    args = parser.parse_args()
    
    raw_infile = args.infile
    print_flag = args.print_tokens
    color_flag = args.no_color

    try:
        # USING UTF-8 TO SUCCESSFULLY READ CHARS LIKE GREEK ETC
        with open(args.infile, "r", encoding="utf-8") as infile:
            run_compiler(raw_infile, infile, print_flag, color_flag)
            sys.exit(0)

    except FileNotFoundError:
        print(f"{Fore.RED}ERROR: File {Fore.LIGHTYELLOW_EX}{args.infile}{Fore.RED} was not found in this directory!")
        sys.exit(1)
    except Exception as e:
        print(f"{Fore.RED}ERROR: {Fore.YELLOW}{e}")
        sys.exit(1)
        
if __name__ == "__main__":
    main()
