from lark import Lark, Transformer
import llvm_ast as my_ast
from codegen import CodeGen
import argparse
import collections


def flatten(x):
    if isinstance(x, collections.Iterable):
        return [a for i in x for a in flatten(i)]
    else:
        return [x]


class TreeToAst(Transformer):

    def __init__(self, module, builder, printf):
        self.symbol_table = {}
        self.stack = []

        self.module = module        # The compilation unit
        self.builder = builder      # The LLVM builder
        self.printf = printf        # Special library functions

    def get_main(self):
        for fn in self.module.functions:
            if fn.name == 'main':
                return fn
        return None

    def funcfirm(self,token):
        return token

    def suite(self,token):
        return token[0]

    def stmt(self,token):
        return token

    def paramlist(self, token):
        #fnty = ir.FunctionType(double, (double, double))
        return token

    def expr_element(self,token):
        return token[0]

    def function(self, tree):

        fn_name = tree[0].name

        if fn_name == 'main':
            for insn in tree[1]:
                insn.eval()

            return self.get_main()
        else:
            fn_arguments = [a.name for a in flatten(tree[1])]
            fn_body = tree[2]

            # create the function
            fn = my_ast.Function(self.builder, self.module, fn_name, fn_arguments, fn_body)
            return fn.eval()

    def function_body(self, token):
        return token

    def statement(self,token):
        print('statement', token)
        return token[0]

    def return_statement(self, token):
        return token[0]

    def factor_(self, token):
        if len(token) == 2 and isinstance(token[1], my_ast.FunctionCall):
            token[1].name = token[0].name
            return token[1]
        else:
            return token[0]

    def function_call_args(self, args):

        return my_ast.FunctionCall(self.builder, self.module, '<un-named>', flatten(args) )

    def expr(self, children):
        print('expr',children)
        if len(children) == 2:
            lhs = children[0]
            rhs_expr = children[1]
            rhs_expr.left = lhs
            return rhs_expr
        else:
            return children[0]

    def arith_mul(self, children):
        rhs = children[0]
        return my_ast.Mul(self.builder, self.module, None, rhs, self.symbol_table)

    def arith_sub(self, children):
        rhs = children[0]
        return my_ast.Sub(self.builder, self.module, None, rhs, self.symbol_table)

    def arith_add(self, children):
        rhs = children[0]
        return my_ast.Sum(self.builder, self.module, None, rhs, self.symbol_table)

    def lhs_assignment(self, children):
        rhs = children[0]
        return my_ast.Assignment(self.builder, self.module, None, rhs, self.symbol_table)

    def array(self, tokens):
        elements = flatten(tokens)
        print('!!!! ARRAY',elements)
        # A Null terminated linked list

        return my_ast.ArrayLiteral(self.builder, self.module, '<un-named>', self.symbol_table, elements)

    def arglist(self, token):
        return token

    def fn_arglist(self,token):
        return token

    def more_args(self, token):
        return token

    def bool_neq(self, token):
        return ['and',token]

    def print_action(self, token):
        print('print_action', token)
        if len(token) == 1:
            return my_ast.Print(self.builder, self.module, self.printf, token[0], [])
        else:
            return my_ast.Print(self.builder, self.module, self.printf, token[0], token[1])



    def factor(self, token):
        return token[0]

    def arguments(self,token):
        return token[0]

    def term(self, children):
        if len(children) == 2:
            lhs = children[0]
            rhs_expr = children[1]
            rhs_expr.left = lhs
            return rhs_expr
        else:
            return children[0]

    def term_(self, children):
            return children[0]

    def identifier(self, token):
        return my_ast.Identifier(self.builder, self.module, token[0].value, self.symbol_table)

    def string(self, token):
        print('string',token)
        return my_ast.String(self.builder, self.module, token[0])

    def number(self,node):
        return node[0]

    def number_(self,token):
        return my_ast.Number(self.builder, self.module, token[0].value)





if __name__ == '__main__':
    """
    ======= M A I N =====
    """
    #try:
    parser = argparse.ArgumentParser(description='Compile a program to LLVM IR.')
    parser.add_argument('input_path', help='Path to input file')
    args = parser.parse_args()


    toylang_grammar = ''
    text = ''

    with open('toylang_ll1.lark', 'r') as myfile:
        toylang_grammar = myfile.read()

    print('starting')

    grammar = Lark(toylang_grammar)

    with open(args.input_path, 'r') as myfile:
        text = myfile.read()

    parse_tree = grammar.parse(text)

    print('parsing done')


    codegen = CodeGen()

    module = codegen.module
    builder = codegen.builder

    printf = codegen.printf

    ast_generator = TreeToAst(module, builder, printf)

    ast_generator.transform(parse_tree)

    print(module)

    print('SYMBOL TABLE', ast_generator.symbol_table)

    codegen.create_ir()
    codegen.save_ir("output.ll")

    #except Exception as e:
    #    print('Compilation error: {}'.format(e))

