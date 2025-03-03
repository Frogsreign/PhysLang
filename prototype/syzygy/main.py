from scanner import *

input = input("Please enter a command: ")
scan = Scanner(input)
scan.scan()
for token in scan.tokens:
    print(token.toString())