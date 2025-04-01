#!/usr/bin/python3

# This module contains functions that extract info from AST variables (e.g. 
# obj1.pos.idx:3) for convenience during compilation.

def parse_var_index(ast_var_index):
    fields = ast_var_index.split(":")
    if len(fields) != 2:
        raise SyntaxError("index must be of the form \"idx:<index>\"")
    return int(fields[1])

def parse_var(ast_var) -> tuple[str, str, int]:
    fields = ast_var.split(".")
    if len(fields) == 2:
        return fields[0], fields[1], 0
    elif len(fields) == 3:
        return fields[0], fields[1], parse_var_index(fields[2])
    else:
        raise SyntaxError("AST variables must be of the form \"<obj>.<prop>[.idx:<index>]\"")
        


