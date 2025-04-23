from syzygy.parse.objs.scanner import *
from syzygy.parse.objs.parser import *
from syzygy.parse.objs.interpreter import *
import json

# TODO: Add file support for many commands

input = input("Please enter a command: ")
scan = Scanner(input)
tokens = scan.scan()
for token in tokens:
    print(token.toString())

parse = Parser(tokens)
statements = parse.parse()
for statement in statements:
    print(statement.toString())

interpret = Interpreter(statements)
interpret.run()

with open("tests/data/sample.json", "w") as outfile:
    json.dump(interpret.dictionary, outfile)

# TODO: Configure the animation from the json file created
# TODO: Streamline access and ability to run the main file w/ a file parameter