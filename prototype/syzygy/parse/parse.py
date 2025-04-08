
from syzygy.parse.funcs import lex
from syzygy.parse.funcs import ast
from syzygy.parse.objs import interpreter
from syzygy.parse.objs import scanner
from syzygy.parse.objs import parser
from syzygy.sim import data_layout

# Factored out in case we change the tree format.
def get_particles(tree: dict):
    return tree["particles"]


def func_expr_to_ast(expr, metadata):
    # lex
    tokens = lex.lex(expr)
    # validate/parse
    if not lex.parse(tokens):
        raise ValueError(f"Invalid expression {expr}")
    # Build AST with norms and dots
    func_ast = ast.tokens_to_ast(tokens)
    # Flatten out norms and dots
    func_ast  = ast.expand_dots(func_ast)
    # Expand dots into indexed sums
    func_ast = ast.collapse_dots(func_ast, metadata)
    return ast


def convert_force_to_ast(force, metadata):
    expr = force["func"]
    force_ast = func_expr_to_ast(expr, metadata)
    # Becomes a subtree of the AST
    force["func"] = force_ast


def convert_update_rule_to_ast(update, metadata):
    expr = update["func"]
    update_ast = func_expr_to_ast(expr, metadata)
    # Becomes a subtree of the AST
    update["func"] = update_ast


def convert_funcs_to_asts(tree: dict):
    particles = get_particles(tree)
    metadata = data_layout.ParticleMetadata(particles)

    for _, force in tree["forces"].items():
        convert_force_to_ast(force, metadata)

    for _, update in tree["update-rules"].items():
        convert_update_rule_to_ast(update, metadata)


def build_entire_ast(script):
    scan = scanner.Scanner(input)
    # Lex
    tokens = scan.scan()
    # Parse
    obj_parser = parser.Parser(tokens)
    statements = obj_parser.parse()
    # Convert to AST
    terp = interpreter.Interpreter(statements)
    terp.run()
    # Convert functions to subtrees
    try:
        convert_funcs_to_asts(interpreter.tree)
    except:
        raise NotImplementedError("Tell Jonas that his interpreter needs a `tree` attribute that contains the AST.")
