from lark import Lark, Transformer

toylang_grammar = ''

with open('toylang.lark', 'r') as myfile:
    toylang_grammar = myfile.read()




print('starting')

grammar = Lark(toylang_grammar)
text ="""
# Fibo


    

fibo(0) : 60 + (5*2).
 
fibo(1) : 1 . 


fibo(0)

fibo(2)

fibo(N | N > 1): 
    fibo( N - 1 ) + fibo( N - 2 ).
    
    
fibo(3)

"""

class TreeToJson(Transformer):

    def __init__(self):
        self.symbol_map = {}

    def funcdef(self,token):
        print('>>>>>>>', token)
        [function_name, parameters] = token[0]
        function_body = token[1]
        entry = {'params': parameters, 'body': function_body}
        if function_name not in self.symbol_map:
            self.symbol_map[function_name] = [entry]
        else:
            self.symbol_map[function_name].append(entry)
            print()
        print('symbol_map', self.symbol_map)

    def funcfirm(self,token):
        return token

    def suite(self,token):
        return token[0]

    def stmt(self,token):
        return token

    def paramlist(self,token):
        return token

    def string(self, (s,)):
        return s[1:-1]

    def number(self, (n,)):
        return float(n)

    def expr_element(self,token):
        return token[0]

    def arith_expr(self,token):
        return token[0]

    def funccall(self,token):
        print(token)
        [function_name,params] = token[0]

        if function_name not in self.symbol_map:
            print('-E- Undefined function {}'.format(function_name))
        else:
            for func in self.symbol_map[function_name]:
                if func['params'] == params:
                    print('executing', func['body'])
                    for insn in func['body']:
                        res = eval(insn)
                        print('>',insn,res,)
                else:
                    print()


        return []

    def expr(self,token):
        return token[0]

    def arith_sub(self, token):
        return '{} - {}'.format(token[0],token[1])

    def arith_add(self, token):
        return '{} + {}'.format(token[0],token[1])

    def arith_mul(self,token):
        return '({} * {})'.format(token[0],token[1])

    def bool_gt(self,token):
        return '{} > {}'.format(token[0],token[1])

    def bool_lt(self,token):
        return '{} < {}'.format(token[0],token[1])

    def boolean_expr(self,token):
        return token

    def identifier(self,token):
        return token[0].value





parse_tree = grammar.parse(text)

TreeToJson().transform(parse_tree)

