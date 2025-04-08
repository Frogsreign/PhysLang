from scanner import *
from parser import *
from interpreter import *
import json

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

with open("syzygy/data/sample.json", "w") as outfile:
    json.dump(interpret.dicts, outfile)

