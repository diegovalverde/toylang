from lark import Lark

toylang_grammar = ''

with open('toylang.lark', 'r') as myfile:
    toylang_grammar = myfile.read()




print('starting')

grammar = Lark(toylang_grammar)
text ="""
# Fibo

main():
    print( fibo(3) ) .
    

fibo(0) : 0 .
 
fibo(1) : 1 . 

fibo(N | N > 1): 
    fibo( N - 1 ) + fibo( N - 2 ).

"""


def run_instruction(t):
    if t.data == 'function_definition':
        print('function definition..')


parse_tree = grammar.parse(text)

for inst in parse_tree.children:
        run_instruction(inst)
