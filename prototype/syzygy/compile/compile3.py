#!/usr/bin/python3

# When reviewing this code, note the following
#
#   1. Seemingly unnecessary 1-3 line functions are actually quite useful when 
#      tweaking local behavior.

from typing import final
import lark
import json
import random
import string

# Initialization and accessors to the op-table (see ops.json).
op_table = None


def init_op_table():
    op_table_reader = open("syzygy/syntax/ops.json", "r")
    global op_table
    op_table = json.JSONDecoder().decode(op_table_reader.read())


def get_op_table():
    if op_table is None:
        raise RuntimeError("op-table was never initialized")
    else:
        return op_table


def get_op_num_args(opcode):
    return get_op_table()[opcode]["num_args"]


def get_op_is_associative(opcode):
    return get_op_table()[opcode]["associative"]


def get_op_format_str(opcode, lang):
    format_str = get_op_table()[opcode]["format"][lang]
    if format_str == 0:
        raise RuntimeError(f"opcode \"{opcode}\" cannot be converted to"
                           "output language \"{lang}\"")
    else:
        return format_str


# Data structures for the compilation process.
class CompileNode:
    def __init__(self):
        self._node = None
        self._expr = None
        self._subs = None
    
    def set_node(self, node):
        self._node = node

    def node(self):
        return self._node

    def set_expr(self, expr):
        self._expr = expr

    def expr(self):
        return self._expr
    
    def set_subs(self, subs):
        self._subs = subs

    def subs(self):
        return self._subs

def is_literal(node):
    return node.data == "literal"

def is_leaf(tree):
    return tree.data in ("literal", "identifier")


# Default initializers for compilation parameters.
def get_default_func_name():
    return "".join(
            random.choices(
                string.ascii_uppercase + string.digits, k=8))

def get_default_compiler_options():
    return {
        "variables_predefined": False,
        "variables": [],
        "variable_types": [],
        "output_lang": "py",
        "var_name_mapper": None
    }


def handle_literal(curr: CompileNode, options):
    #print("LITERAL: ", curr.node())
    tree = curr.node()
    curr.set_expr(str(tree.children[0]))


def handle_identifier(curr, options):
    tree = curr.node()
    #print("IDENTIFIER: ", curr.node())
    if len(curr.node().children) == 1:
        curr.set_expr("dt");
        return

    particle_name, prop_name, prop_idx = tree.children
    particle_name = particle_name.children[0]
    prop_name = prop_name.children[0]

    #print("PROP IDX: ", tree)

    if prop_idx is not None:
        prop_idx = prop_idx.children[0]
    else:
        prop_idx = 0

    ast_var_name = f"{particle_name}.{prop_name}[{prop_idx}]"
    if options["variables_predefined"]:
        # Map this sequence to the correct value somehow.
        # Option 1: 
        #   - Store properties in a massive static array.
        #   - Map object names to indices.
        #   - pass user-defined functions a pointer to the array.
        #   - replace this value with a literal reference.
        #
        # Option 1 works well since all values are initialized at 
        # runtime.
        # 
        # We'd need to pass in the variable-to-index map to the 
        # compiler.
        converter = options["var_name_mapper"]
        if converter is None:
            raise RuntimeError("No variable mapper provided.")
        curr.set_expr(converter(ast_var_name))
    else:   
        options["variables"].append(ast_var_name)
        curr.set_expr(ast_var_name)


# Formatting utilities.
def format_arg_list(variables, lang):
    if lang == "py":
        return ", ".join(variables)
    elif lang == "c":
        return ", ".join([f"{k} {v}" for k, v in variables.items()])
    else:
        return NotImplemented


def format_function_definition(expr, options):
    lang = options["output_lang"]
    if "func_name" in options:
        func_name = options["func_name"]
    else:
        func_name = get_default_func_name()
    arg_list = format_arg_list(options["variables"], lang) 
    if lang == "py":
        func_code = "lambda " + arg_list + ": " + expr
    elif lang == "c":
        # Return type = float for now. Return types should be determined
        # by the user, possibly implicitly.
        func_code = " ".join([
            "float", func_name, f"({arg_list})", "{", 
            "return", expr, ";", 
            "}"])
    else:
        return NotImplemented
    return func_name, func_code


def format_expr(opcode, subs, options):
    lang = options["output_lang"]
    expr = get_op_format_str(opcode, lang)
    for i in range(get_op_num_args(opcode)):
        expr = expr.replace(f"%{i}", subs[i])
    return expr


# Compilation control flow facilitation routines.
def handle_nonterminal_expr(node, options):
    tree = node.node()
    

    if tree.data == "add": opcode = "+"
    if tree.data == "sub": opcode = "-"
    if tree.data == "mul": opcode = "*"
    if tree.data == "div": opcode = "/"
    if tree.data == "pow": opcode = "^"


    subexprs = [sub.expr() for sub in node.subs()]
    return format_expr(opcode, subexprs, options)


def handle_terminal_expr(curr, options):
    if is_literal(curr.node()):
        handle_literal(curr, options)
    else:
        handle_identifier(curr, options)


def init_subexpr(operand, options):
    sub = CompileNode()
    sub.set_node(operand)
    return sub


def process_subexprs(curr, stack, options):
    # Push subexpressions onto the stack
    tree = curr.node()
    operands = tree.children
    subs = []
    for operand in operands:
        child = init_subexpr(operand, options=options)
        subs.append(child)
        stack.append(child)
    # When DFS returns to this node, all subs will be compiled (have 
    # defined `expr` fields), and the other branch will execute.
    curr.set_subs(subs)


# Compilation entry point.
def compile_tree(
        syntax_tree: lark.Tree, 
        compiler_options=None):
    """
    Convert the syntax tree to a compiled (python bytecode) python 
    lambda.

    Args:
        syntax_tree (list): A bracketted syntax tree.
        func_name (str): The function's name.
        variables (list): A list of str instances that become arguments 
        to the returned function.

    Returns:
        tuple[str, str]: The function name, and the function code.
    """
    # Initializations --------------------------------------------------
    init_op_table()
    root = CompileNode()
    root.set_node(syntax_tree)


    # Strip `start` symbol and other nonsense


    # Validate keyword args --------------------------------------------
    # Validate `options`
    options = get_default_compiler_options()
    if compiler_options is not None:
        for k, v in compiler_options.items():
            options[k] = v

    # DFS for compilation ----------------------------------------------
    stack = [root]
    while len(stack) > 0:
        curr = stack[-1]
        if is_leaf(curr.node()):
            #print("LEAF: ", curr.node())
            handle_terminal_expr(curr, options=options)
            stack.pop()
        elif curr.subs() == None:
            #print("NOT LEAF: ", curr.node())
            # Create subexpressions, assign them to the current node, 
            # and push them onto the stack to be processed.
            process_subexprs(curr, stack, options=options)
        else:

            if curr.node().data == "start":
                final_expr = curr.subs()[0].expr()
                break
            expr = handle_nonterminal_expr(curr, options=options)
            curr.set_expr(expr)
            stack.pop()


    # Create function signature ----------------------------------------
    func_name, func_code = format_function_definition(final_expr, options)

    print("FINAL EXPR: ", func_code)

    return func_name, func_code
