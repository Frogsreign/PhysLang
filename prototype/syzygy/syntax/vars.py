#!/usr/bin/python3

# This module contains functions that extract info from AST variables (e.g. 
# obj1.pos.idx:3) for convenience during compilation.

def parse_var_index(ast_var_index):
    fields = ast_var_index.split(":")
    if len(fields) != 2:
        raise SyntaxError("index must be of the form \"idx:<index>\"")
    return int(fields[1])

def parse_var(ast_var) -> tuple[str, str, int]:
    particle_name, prop_name = ast_var.split(".")
    
    if prop_name.endswith("]"):
        prop_name = prop_name[:-1]
        prop_name, prop_idx = prop_name.split("[")
    else:
        prop_idx = 0

    return particle_name, prop_name, int(prop_idx)



