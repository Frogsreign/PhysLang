#!/usr/bin/python3
#
# @author Jacob Leider
#
#
# The Syzygy `step` Compiler
#

import lark
import random
import string


# Default initializers for compilation parameters.
def get_default_func_name():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


def get_default_compiler_options():
    return {
        "variables_predefined": False,
        "variables": [],
        "variable_types": [],
        "output_lang": "py",
        "var_name_mapper": None
    }


def format_binary_operation(leftexpr, rightexpr, op):
    return f"({leftexpr}) {op} ({rightexpr})"


# Compiles functions to python lambdas.
class SyzygyFunctionCompiler(lark.Visitor):
    def __init__(self, compiler_options):
        self.compiler_options = compiler_options


    def give_token_expr(*args):
        for arg in args:
            if isinstance(arg, lark.Token):
                if hasattr(arg, 'expr'):
                    raise Exception("Already has expr attribute")
                arg.expr = str(arg.value)


    def start(self, tree):
        child = tree.children[0]
        tree.expr = child.expr


    def identifier(self, tree):
        child = tree.children[0]
        tree.expr = child.expr


    def keyword(self, tree):
        # TODO: Make sure keyword is in `parameters`
        child = tree.children[0]
        tree.expr = child


    def particle_property_access(self, tree):
        # TODO: Make sure particle_property_access is in `parameters`
        particle_name, prop_name, prop_index = tree.children

        particle_name = particle_name.value
        prop_name = prop_name.value
        prop_index = prop_index.value

        particle_size = self.compiler_options["particle_metadata"].particle_size
        # TODO: Casting to `int` is a temporary fix. This function should 
        # assume `prop_index` is int and throw otherwise.
        prop_offset = self.compiler_options["particle_metadata"].prop_offset(prop_name) + int(prop_index)
        acc = f"data[{particle_name} * {particle_size} + {prop_offset}]"
        tree.expr = acc 


    def literal(self, tree):
        child = tree.children[0]
        tree.expr = child


    def abs(self, tree):
        print("Abs " + 80 * '-')
        print(tree.pretty())
        child = tree.children[0]
        tree.expr = f"abs({child.expr})"


    def add(self, tree):
        left, right = tree.children
        tree.expr = format_binary_operation(left.expr, right.expr, "+")


    def mul(self, tree):
        left, right = tree.children
        tree.expr = format_binary_operation(left.expr, right.expr, "*")


    def sub(self, tree):
        left, right = tree.children
        tree.expr = format_binary_operation(left.expr, right.expr, "-")


    def div(self, tree):
        left, right = tree.children
        tree.expr = format_binary_operation(left.expr, right.expr, "/")


    def pow(self, tree):
        left, right = tree.children
        tree.expr = format_binary_operation(left.expr, right.expr, "**")


    # TODO: Needs testing
    def step(self, tree):
        child = tree.children[0]
        tree.expr = f"0 if ({child.expr}) < 0 else 1"


    # TODO: Needs testing
    def sign(self, tree):
        child = tree.children[0]
        tree.expr = f"-1 if ({child.expr}) < 0 else 1"


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


# Compilation entry point.
# TODO: REPLACE WITH LARK VISITOR
def compile_tree(
        syntax_tree: lark.Tree, 
        compiler_options=None):
    """
    Convert the syntax tree to a compiled (python bytecode) python 
    lambda.

    Args:
        syntax_tree (lark.Tree): A lark parse-tree
        func_name (str): The function's name.
        variables (list): A list of str instances that become arguments 
        to the returned function.

    Returns:
        tuple[str, str]: The function name, and the function code.
    """
    # Validate keyword args --------------------------------------------
    # Validate `options`
    options = get_default_compiler_options()
    if compiler_options is not None:
        for k, v in compiler_options.items():
            options[k] = v

    # Check for required options
    if "particle_metadata" not in options:
        raise Exception("`compiler_options` must contain an entry for \"particle_metadata\"")

    func_compiler = SyzygyFunctionCompiler(options)
    func_compiler.visit(syntax_tree)

    # Create function signature ----------------------------------------
    func_name, func_code = format_function_definition(syntax_tree.expr, options)

    print(func_code)

    return func_name, func_code
