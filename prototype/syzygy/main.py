from scanner import *
from parser import *

input = input("Please enter a command: ")
scan = Scanner(input)
tokens = scan.scan()
for token in tokens:
    print(token.toString())

parse = Parser(tokens)
statements = parse.parse()
for statement in statements:
    print(statement.toString())