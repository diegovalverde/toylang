from llvmlite import ir


class Number:
    def __init__(self, builder, module, value):
        self.builder = builder
        self.module = module
        self.value = value

    def __repr__(self):
        return 'Number({})'.format(self.value)

    def set_builder(self, builder):
        self.builder = builder

    def eval(self):
        i = ir.Constant(ir.IntType(32), int(self.value))
        return i


class ArrayLiteral:
    """
    Essentially a NULL terminated linked list
    """
    def __init__(self, builder, module, name, symbol_table, elements):
        self.builder = builder
        self.module = module
        self.name = name
        self.symbol_table = symbol_table
        self.elements = elements

    def eval(self):
        symbol_name = '{}__ARRAY__{}'.format(self.builder.function.name, self.name)

        # Use this: Immutable

        int32 = ir.IntType(32)
        null = 0
        # A = ir.Constant.literal_array((ir.Constant(int32, 1), ir.Constant(int32, 2), ir.Constant(int32, 3)))
        # then
        # value = self.builder.extract_value(A,3)

        # type, i32 * head, i32 * tail
        t_node = ir.LiteralStructType((ir.IntType(8), int32, ir.PointerType(32)))
        #t_node type is: { float*, i32 }*.
        # That is, %t_node is a pointer to a structure containing a pointer to a byte, int32  and an i32*.

        # create a pointer to the head
        p_type = ir.PointerType(t_node)
        p = self.builder.alloca(p_type)

        # fty = ir.FunctionType(ir.IntType(32), [ir.IntType(32), ir.IntType(32)])
        # args = (self.elements[0].eval(), self.elements[1].eval())
        # add = self.builder.asm(fty, "mov $2, $0\nadd $1, $0", "=r,r,r",args, '',name="asm_add")

        print(self.module)

        # Allocate n elements
        allocation = self.builder.alloca(t_node, size=len(self.elements))

        #print(symbol_name, self.module)

        for i in range(len(self.elements)):
            idx = ir.Constant(int32, i)
            print('2',symbol_name, self.module)

            p_element_type = self.builder.alloca(ir.PointerType(8))
            p_value = self.builder.gep(allocation, [idx, idx])
            print('>>>>>>>',p_value, symbol_name, self.module)
            p_ptr_next = self.builder.gep(allocation, [ir.Constant(int32, 1)])
            print(symbol_name, self.module)
            self.builder.store(ir.Constant(ir.IntType(8), self.elements[i].eval()),p_value)

            print('.......',symbol_name, self.module)

            if i + 1 == len(self.elements):
                self.builder.store(p_ptr_next, ir.Constant(p_type, null))
            else:
                idx_next = ir.Constant(p_type, i+1)
                p_next = self.builder.gep(allocation, idx_next)
                self.builder.store(p_ptr_next, ir.Constant(p_type, p_next))

            #print(e)


        #p = self.builder.alloca(p_type, name=symbol_name, )


        #a = ir.ArrayType(ir.IntType(32), self.size)
        return allocation


class Identifier:
    def __init__(self, builder, module, name, symbol_table):
        self.builder = builder
        self.module = module
        self.name = name
        self.symbol_table = symbol_table

    def __repr__(self):
        return 'Identifier({})'.format(self.name)

    def set_builder(self, builder):
        self.builder = builder

    def eval(self):
        # Check the current function that we are building
        # To see if the identifier is a function argument
        for arg in self.builder.function.args:
            if arg.name == self.name:
                return arg

        symbol_name = '{}__{}'.format(self.builder.function.name, self.name)
        # Now check to see if it is a local (function scope) variable
        if symbol_name in self.symbol_table:
            return self.builder.load(self.symbol_table[symbol_name])


        # Todo check is already allocated symbol in the Symbol Table

        # Not an argument, then  must be something new
        allocation = self.builder.alloca(ir.IntType(32), name=self.name)
        self.symbol_table[symbol_name] = allocation
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
    def __repr__(self):
        return 'Sum({} , {})'.format(self.left, self.right)

    def eval(self):
        return self.builder.add(self.left.eval(), self.right.eval())


class Mul(BinaryOp):
    def __repr__(self):
        return 'Mul({} , {})'.format(self.left, self.right)

    def eval(self):
        return self.builder.mul(self.left.eval(), self.right.eval())


class Sub(BinaryOp):
    def __repr__(self):
        return 'Sub({} , {})'.format(self.left, self.right)

    def eval(self):
        i = self.builder.sub(self.left.eval(), self.right.eval())
        return i


class Div(BinaryOp):
    def __repr__(self):
        return 'Div({} , {})'.format(self.left, self.right)

    def eval(self):
        i = self.builder.sdiv(self.left.eval(), self.right.eval())
        return i


class Assignment(BinaryOp):
    def eval(self):
        name = self.left.name

        symbol_name = '{}__{}'.format(self.builder.function.name, name)

        if symbol_name in self.symbol_table:
            raise Exception('Cannot re-assign to {}. Variables are Immutable'.format(name))

        allocation = self.builder.alloca(ir.IntType(32), name=name)
        self.symbol_table[symbol_name] = allocation
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


class String:
    def __init__(self, builder, module, fmt_str):
        self.builder = builder
        self.module = module
        self.fmt_str = '{}\n\0'.format(fmt_str[1:-1])

    def __repr__(self):
        return 'String({})'.format(self.fmt_str)

    def eval(self):
        return ir.Constant(ir.ArrayType(ir.IntType(8), len(self.fmt_str)),
                           bytearray(self.fmt_str.encode("utf8")))


class Print:
    def __init__(self, builder, module, printf, fmt_str, arg_list):
        self.builder = builder
        self.module = module
        self.printf = printf
        self.fmt_str = fmt_str
        self.arg_list = arg_list

    def eval(self):
        values = [v.eval() for v in self.arg_list]
        c_fmt = self.fmt_str.eval()

        voidptr_ty = ir.IntType(8).as_pointer()

        local_fmt = self.builder.alloca(c_fmt.type, name="fstr")
        self.builder.store(c_fmt, local_fmt)

        fmt_arg = self.builder.bitcast(local_fmt, voidptr_ty)

        if len(values) == 1:
            return self.builder.call(self.printf, [fmt_arg, values[0]])
        else:
            return self.builder.call(self.printf, [fmt_arg])
