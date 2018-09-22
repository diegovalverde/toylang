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


def remove_invalid(L):
    return [x for x in L if x is not None]


class TreeToAst(Transformer):

    def __init__(self, module, builder, printf, debug=False):
        self.symbol_table = {}
        self.stack = []

        self.module = module        # The compilation unit
        self.builder = builder      # The LLVM builder
        self.printf = printf        # Special library functions
        self.debug = debug
        self.function_map = {}
        self.function_definition_list = []
        self.main = None

    def get_main(self):
        for fn in self.module.functions:
            if fn.name == 'main':
                return fn
        return None

    def funcfirm(self,token):
        return token

    def suite(self,token):
        return token[0]

    def statement(self, token):
        if self.debug:
            print(token)

        return token

    def paramlist(self, token):
        #fnty = ir.FunctionType(double, (double, double))
        return token

    def expr_element(self,token):
        return token[0]

    def function(self, tree):


        fn_name = tree[0].name

        if fn_name == 'main':
            self.main = tree[1]
        else:

            fn_arguments = []
            firm = remove_invalid(flatten(tree[1]))
            print('----->', firm)

            preconditions = None
            if isinstance(firm[-1], my_ast.BinaryOp):
                preconditions = firm[-1]
                firm.pop()

            fn_arguments = [e.name for e in firm]
            arity = len(fn_arguments)
            fn_body = flatten(tree[2])
            function_key = '{}_arity_{}'.format(fn_name, arity)

            clause = my_ast.FunctionClause(function_key, fn_body, preconditions )

            if function_key not in self.function_map:
                self.function_definition_list.append(function_key)
                self.function_map[function_key] = my_ast.FunctionMap(self.builder, self.module, function_key,
                                                                     self.printf, fn_arguments)
            self.function_map[function_key].clauses.append(clause)


    def fn_precondition(self, token):
        return token

    def function_body(self, token):
        return token

    def statement(self,token):
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

    def expr_handler(self, token):
        children = remove_invalid(flatten(token))

        if self.debug:
            print(children)

        if len(children) == 2:
            lhs = children[0]
            rhs_expr = children[1]
            rhs_expr.left = lhs
            return rhs_expr
        else:
            return children[0]

    def expr(self, token):
        return self.expr_handler(token)

    def boolean_expr(self, token):

        return self.expr_handler(token)

    def arith_mul(self, children):
        rhs = children[0]
        return my_ast.Mul(self.builder, self.module, None, rhs, self.symbol_table)

    def bin_op(self, token, ast_op):
        children = remove_invalid(flatten(token))

        if len(children) == 0:
            return None
        elif len(children) == 1:
            return ast_op(self.builder, self.module, None, children[0], self.symbol_table)
        elif len(children) == 2:
            children[1].left = children[0]
            return ast_op(self.builder, self.module, None, children[1], self.symbol_table)
        else:
            return None

    def arith_sub(self, token):
        return self.bin_op(token, my_ast.Sub)

    def arith_add(self, token):
        return self.bin_op(token, my_ast.Sum)

    def arith_div(self, token):
        return self.bin_op(token, my_ast.Div)

    def arith_mod(self,token):
        print('arith_mod',token)
        return self.bin_op(token[0], my_ast.Mod)

    def lhs_assignment(self, children):
        rhs = children[0]
        return my_ast.Assignment(self.builder, self.module, None, rhs, self.symbol_table)

    def expr_rhs(self, tokens):
        if len(tokens) == 1:
            return tokens[0]
        else:
            return None

    def array(self, tokens):
        elements = flatten(tokens)

        # A Null terminated linked list

        return my_ast.ArrayLiteral(self.builder, self.module, '<un-named>', self.symbol_table, elements)

    def arglist(self, token):
        return token

    def fn_arglist(self, token):
        print('fn_arglist',token)
        return token

    def more_args(self, token):
        return token

    def bool_gt(self, token):
        return self.bin_op(token, my_ast.GreaterThan)

    def bool_and(self, token):
        return self.bin_op(token, my_ast.And)

    def bool_eq(self, token):
        return self.bin_op(token, my_ast.EqualThan)

    def bool_lt(self,token):
        return self.bin_op(token, my_ast.LessThan)

    def boolean_binary_term(self, token):
        if len(token) == 2:
            token[1].left = token[0]
            print('boolean_term',token[1])
            return token[1]
        else:
            return token[0]

    def boolean_binary_term_(self,token):
        if len(token) == 2:
            token[1].left = token[0]
            print('boolean_binary_term_', token[1])
            return token[1]
        else:
            return token[0]

    def bool_factor(self,token):
        return token[0]

    def boolean_expr(self,token):
        print('boolean_expr', token)
        if len(token) == 2:
            token[1].left = token[0]
            print('boolean_expr',token[1])
            return token[1]
        else:
            return token[0]

    def print_action(self, token):
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
    parser.add_argument('--debug', action='store_true', default=False, help='For tool debugging purposes only')
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

    ast_generator = TreeToAst(module, builder, printf, debug=args.debug)

    ast_generator.transform(parse_tree)

    for fn in ast_generator.function_definition_list:
        print('-I- Emitting Function {} '.format(fn))
        ast_generator.function_map[fn].eval()

    if ast_generator.main is None:
        print('Where is main??')
    else:
        for insn in ast_generator.main:
           insn.eval()



    codegen.create_ir()
    codegen.save_ir("output.ll")

    if args.debug:
        print(module)

    #except Exception as e:
    #    print('Compilation error: {}'.format(e))

