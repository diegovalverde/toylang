from lark import Lark, Transformer

class TreeToJson(Transformer):
    """
    Usar notacion polaca inversa
    """

    def __init__(self):
        self.symbol_map = {}
        self.stack = []

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
            for firm in self.symbol_map[function_name]:

                if firm['params'] == params:
                    print('executing', firm['body'])
                    for insn in firm['body']:
                        res = eval(insn)
                        print('>',insn,res,)
                else:
                    print('>>>>>>>',firm['params'] )



                    last_function_param = firm['params'][-1]
                    if isinstance(last_function_param, list):
                        constrains_satisfied = True
                        bool_condition_list = last_function_param
                        for i in range(len(bool_condition_list)):
                            print(['set',firm['params'][i],params[i]])
                            print(bool_condition_list[i])
                            print(['jnz','label_not_met'])


                        print('call',function_name)
                        if constrains_satisfied:
                            #Execute
                            for insn in firm['body']:
                                print('???',insn)
                                for param in firm['params'][:-1]:
                                    insn = insn.replace(firm['params'][i], str(params[i]))
                                print('???2',insn)

                                print('>', insn)

                            print('Has boolean stuff')

                    if len(params) == len(firm['params'] ):
                        for param in firm['params']:
                            if not isinstance(param ,str):
                                continue
                            print('PAR',param)


        return []

    def expr(self,token):
        return token[0]

    def arith_sub(self, token):
        return ['sub',token[0], token[1]]

    def arith_add(self, token):
        return '{} + {}'.format(token[0],token[1])

    def arith_mul(self,token):
        return '({} * {})'.format(token[0],token[1])

    def bool_gt(self,token):
        return ['cmp_gt',token[0],token[1]]
        return '{} > {}'.format(token[0],token[1])

    def bool_lt(self,token):
        return '{} < {}'.format(token[0],token[1])

    def boolean_expr(self,token):
        return token

    def identifier(self,token):
        return token[0].value


if __name__ == '__main__':
    toylang_grammar = ''
    text = ''

    with open('toylang.lark', 'r') as myfile:
        toylang_grammar = myfile.read()

    print('starting')

    grammar = Lark(toylang_grammar)
    with open('fibo.toy', 'r') as myfile:
        text = myfile.read()

    parse_tree = grammar.parse(text)

    TreeToJson().transform(parse_tree)

