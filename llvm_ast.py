from llvmlite import ir


class Number:
    def __init__(self, builder, module, value):
        self.builder = builder
        self.module = module
        self.value = value

    def set_builder(self, builder):
        self.builder = builder

    def eval(self):
        i = ir.Constant(ir.IntType(32), int(self.value))
        return i


class Identifier:
    def __init__(self, builder, module, name, symbol_table):
        self.builder = builder
        self.module = module
        self.name = name
        self.debug = True
        self.symbol_table = symbol_table

    def set_builder(self, builder):
        self.builder = builder

    def eval(self):
        # Check the current function that we are building
        # To see if the identifier is a function argument
        for arg in self.builder.function.args:
            if arg.name == self.name:
                return arg

        # Now check to see if it is a local (function scope) variable
        if self.name in self.symbol_table:
            return self.builder.load(self.symbol_table[self.name])


        # Todo check is already allocated symbol in the Symbol Table

        # Not an argument, then  must be something new
        allocation = self.builder.alloca(ir.IntType(32), name=self.name)
        self.symbol_table[self.name] = allocation
        return self.builder.load(allocation)


class BinaryOp:
    def __init__(self, builder, module, left, right, symbol_table):
        self.builder = builder
        self.module = module
        self.left = left
        self.right = right
        self.symbol_table = symbol_table

    def set_builder(self,builder):
        self.builder = builder
        self.left.set_builder(builder)
        self.right.set_builder(builder)


class Sum(BinaryOp):
    def eval(self):
        return self.builder.add(self.left.eval(), self.right.eval())


class Mul(BinaryOp):
    def eval(self):
        return self.builder.mul(self.left.eval(), self.right.eval())


class Sub(BinaryOp):
    def eval(self):
        i = self.builder.sub(self.left.eval(), self.right.eval())
        return i


class Assignment(BinaryOp):
    def eval(self):
        name = self.left.name

        if name in self.symbol_table:
            raise Exception('Cannot re-assign to {}. Variables are Immutable'.format(name))

        allocation = self.builder.alloca(ir.IntType(32), name=name)
        self.symbol_table[name] = allocation
        # Evaluate whatever was on the RHS
        rhs_result = self.right.eval()
        # Store it in our variable

        return self.builder.store(rhs_result, allocation)


class FunctionCall:
    def __init__(self, builder, module, name, args):
        self.builder = builder
        self.module = module
        self.name = name
        self.args = args

    def set_builder(self, builder):
        self.builder = builder

    def eval(self):
        found = False
        for fn in self.module.functions:
            if fn.name == self.name:
                return self.builder.call(fn, [a.eval() for a in self.args])

        if not found:
            raise Exception('Undeclared function \'{}\' '.format(self.name))

        return None


class Function:
    def __init__(self, builder, module, name, args, fn_body):
        self.builder = builder
        self.module = module
        self.name = name
        self.args = args
        self.arg_types = [ir.IntType(32)]*len(args)  # Assume all arguments are double for now
        self.fn_body = fn_body

    def eval(self):
        func_type = ir.FunctionType(ir.IntType(32), self.arg_types, False)
        fn = ir.Function(self.module, func_type, name=self.name)

        for i in range(len(self.args)):
            fn.args[i].name = self.args[i]

        ret_stmt = self.fn_body[-1]
        fn_stmts = self.fn_body[:-1]
        # Now implement the function
        block = fn.append_basic_block(name="entry")
        builder = ir.IRBuilder(block)

        for stmt in fn_stmts:
            stmt.set_builder(builder)
            stmt.eval()

        # By convention the last statement in the function is the return statement
        ret_stmt.set_builder(builder)
        builder.ret(ret_stmt.eval())
        return fn


class Print:
    def __init__(self, builder, module, printf, value):
        self.builder = builder
        self.module = module
        self.printf = printf
        self.value = value

    def eval(self):
        value = self.value.eval()

        # Declare argument list
        voidptr_ty = ir.IntType(8).as_pointer()
        fmt = "%i \n\0"
        c_fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
                            bytearray(fmt.encode("utf8")))
        global_fmt = ir.GlobalVariable(self.module, c_fmt.type, name="fstr")
        global_fmt.linkage = 'internal'
        global_fmt.global_constant = True
        global_fmt.initializer = c_fmt
        fmt_arg = self.builder.bitcast(global_fmt, voidptr_ty)

        # Call Print Function
        self.builder.call(self.printf, [fmt_arg, value])
