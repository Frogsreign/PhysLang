
import funcs.lex
import funcs.ast
import objs.interpreter
import objs.scanner
import objs.parser
from syzygy.sim import data_layout

# Factored out in case we change the tree format.
def get_particles(tree: dict):
    return tree["particles"]


def func_expr_to_ast(expr, metadata):
    # lex
    tokens = funcs.lex.lex(expr)
    # validate/parse
    if not funcs.lex.parse(tokens):
        raise ValueError(f"Invalid expression {expr}")
    # Build AST with norms and dots
    ast = funcs.ast.tokens_to_ast(tokens)
    # Flatten out norms and dots
    ast = funcs.ast.expand_dots(ast)
    # Expand dots into indexed sums
    ast = funcs.ast.collapse_dots(ast, metadata)
    return ast


def convert_force_to_ast(force, metadata):
    expr = force["func"]
    ast = func_expr_to_ast(expr, metadata)
    # Becomes a subtree of the AST
    force["func"] = ast


def convert_update_rule_to_ast(update, metadata):
    expr = update["func"]
    ast = func_expr_to_ast(expr, metadata)
    # Becomes a subtree of the AST
    update["func"] = ast


def convert_funcs_to_asts(tree: dict):
    particles = get_particles(tree)
    metadata = data_layout.ParticleMetadata(particles)

    for _, force in tree["forces"].items():
        convert_force_to_ast(force, metadata)

    for _, update in tree["update-rules"].items():
        convert_update_rule_to_ast(update, metadata)


def build_entire_ast(script):
    scan = objs.scanner.Scanner(input)
    # Lex
    tokens = scan.scan()
    # Parse
    obj_parser = objs.parser.Parser(tokens)
    statements = obj_parser.parse()
    # Convert to AST
    interpreter = objs.interpreter.Interpreter(statements)
    interpreter.run()
    # Convert functions to subtrees
    try:
        convert_funcs_to_asts(interpreter.tree)
    except:
        raise NotImplementedError("Tell Jonas that his interpreter needs a `tree` attribute that contains the AST.")
