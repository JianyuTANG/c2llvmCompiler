import sys
from antlr4 import *
from parser_.CLexer import CLexer
from parser_.CParser import CParser
from parser_.CVisitor import CVisitor
from llvmlite import ir
import re
from SymbolTable import *


def addIndentation(a, num=2):
    return '\n'.join([' ' * num + i for i in a.split('\n')])


class ToJSVisitor(CVisitor):
    BASE_TYPE = 0
    ARRAY_TYPE = 1
    FUNCTION_TYPE = 2

    CHAR_TYPE = ir.IntType(8)
    INT_TYPE = ir.IntType(32)
    FLOAT_TYPE = ir.FloatType()
    DOUBLE_TYPE = ir.DoubleType()
    VOID_TYPE = ir.VoidType()
    BOOL_TYPE = ir.IntType(1)

    def __init__(self):
        # Create some useful types
        # double = ir.DoubleType()
        # self.fnty = ir.FunctionType(double, (double, double))

        # Create an empty module...
        self.module = ir.Module()
        self.symbol_table = SymbolTable(None)
        # ir.GlobalVariable(self.module, ir.IntType(32), name="glo")
        # and declare a function named "fpadd" inside it
        # self.func = ir.Function(self.module, self.fnty, name="fpadd")
        #ir.GlobalVariable(self.module, ir.IntType(32), name="glo")
        # Now implement the function
        # self.block = self.func.append_basic_block(name="entry")
        # self.builder = ir.IRBuilder(self.block)
        # a, b = self.func.args
        # result = self.builder.fadd(a, b, name="res")
        # self.builder.ret(result)
        # self.builder.alloca(ir.IntType(32),name="aaa")
        # a=self.builder.alloca(ir.IntType(32), name="aab")
        # self.builder.store(ir.IntType(32)(9),a)

    def visitCompilationUnit(self, ctx):
        for i in ctx.children:
            self.visit(i)
        # ans = [self.visit(i) for i in ctx.children[:-1]]
        # ans = [x for x in ans if x]
        # return '\n'.join(ans) # + '\nmain();\n'

    def visitFunctionDefinition(self, ctx):
        '''
        functionDefinition
        :   declarationSpecifiers? declarator declarationList? compoundStatement
        ;
        不考虑 declarationList
        :param ctx:
        :return:
        '''
        assert ctx.declarationList() == None
        _type = self.visit(ctx.declarationSpecifiers())
        # self.visit(ctx.declarator())
        name, params = self.visit(ctx.declarator())
        args = [i for i, j in params]
        fnty = ir.FunctionType(_type, args)
        func = ir.Function(self.module, fnty, name=name)
        block = func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)
        # 创建子符号表
        self.symbol_table = createTable(self.symbol_table)
        func_args = func.args
        arg_names = [j for i, j in params]
        assert len(arg_names) == len(func_args)
        for seq, name in enumerate(arg_names):
            arg = func_args[seq]
            arg_ptr = self.builder.alloca(arg.type, name=name)
            self.builder.store(arg, arg_ptr)
            self.symbol_table.insert(name, value=arg_ptr)
        self.visit(ctx.compoundStatement())
        # 退回父符号表
        self.symbol_table = self.symbol_table.getFather()


    # def visitDeclarationSpecifiers(self, ctx):
    #     if ctx.CONST():
    #         return 'const'
    #     return 'let'

    def visitDeclarator(self, ctx: CParser.DeclaratorContext):
        # if ctx.directDeclarator():
        return self.visit(ctx.directDeclarator())

    def visitDirectDeclarator(self, ctx: CParser.DirectDeclaratorContext):
        """
            directDeclarator
                :   Identifier
                |   directDeclarator '[' assignmentExpression? ']'
                |   directDeclarator '(' parameterTypeList ')'
                ;
            :param ctx:
            :return:声明变量的类型，名字name,llvm类型,
                    如果是变量是函数FUNTION_TYPE，则还会返回所有参数的名字arg_names
                    如果变量是数组ARRAY_TYPE，会返回数组范围列表
                    如果变量是普通类型BASE_TYPE,会返回一个空列表
        """
        if ctx.Identifier():
            name = self.visit(ctx.Identifier())
            btype = (self.BASE_TYPE, None)
            self.symbol_table.insert(name, btype)
            return name
        elif ctx.children[1].getText() == '[':
            name = self.visit(ctx.directDeclarator())
            if ctx.assignmentExpression():
                length = self.visit(ctx.assignmentExpression())
                btype = (self.ARRAY_TYPE, length)
            else:
                pass
            self.symbol_table.insert(name, btype=btype)
            return name
        elif ctx.children[1].getText() == '(':
            name = self.visit(ctx.directDeclarator())
            btype = (self.FUNCTION_TYPE, None)
            self.symbol_table.insert(name, btype)
            if ctx.parameterTypeList():
                params = self.visit(ctx.parameterTypeList())
            else:
                params = []
            return name, params

        # if ctx.Identifier():
        #     return ctx.getText()
        #
        # if ctx.LeftParen().getText() == '(':
        #     name = self.visit(ctx.directDeclarator())
        #     params = self.visit(ctx.parameterTypeList())
        #     return name, params
            # 函数声明
            # name, ret_tp, pms = self.visitDirectDeclarator(
            #     ctx.directDeclarator())

            # ret_tp = ir.FunctionType(ret_tp, pms)
            # if ctx.children[2].getText() == ')':
            #     # 无参数 形如a()
            #     return name, ret_tp, []
            # elif ctx.children[2].getRuleIndex() == CParser.parameterTypeList:
            #     # 有参数 形如a(int, char, ...)
            #     pass

    # def visitTypeSpecifier(self, ctx):
    #     if ctx.CONST():
    #         return 'const'
    #     return 'let'

    # def visitPureIdentifier(self, ctx: CParser.DeclaratorContext):
    #     return ctx.directDeclarator().Identifier().getText()

    # def visitArrayIdentifier(self, ctx:CParser.ArrayIdentifierContext):
    #     if ctx.assignmentExpression():
    #         # array definition
    #         length = self.visit(ctx.assignmentExpression())
    #         return f'{ctx.Identifier().getText()} = new Array({length})'
    #     else:
    #         # string definition
    #         return f'{ctx.Identifier().getText()}'        

    def visitFunctionDefinitionOrDeclaration(self, ctx: CParser.FunctionDefinitionContext):
        if ctx.declarationList():
            return f'{ctx.declarator().directDeclarator().Identifier().getText()}({self.visit(ctx.declarationList())})'
        return f'{ctx.declarator().directDeclarator().Identifier().getText()}()'

    def visitTypeSpecifier(self, ctx):
        _type = {
            'int': self.INT_TYPE,
            'char': self.CHAR_TYPE,
            'float': self.FLOAT_TYPE,
            'double': self.DOUBLE_TYPE,
            'void': self.VOID_TYPE
        }.get(ctx.getText())
        return _type

    def visitDeclarationSpecifiers(self, ctx):
        return self.visit(ctx.children[-1])

    def visitDeclaration(self, ctx):
        _type = self.visit(ctx.declarationSpecifiers())
        declarator_list = self.visit(ctx.initDeclaratorList())
        for name, init_val in declarator_list:
            if isinstance(name, tuple):
                # 函数类型
                _func = name
                name = _func[0]
                params = _func[1]
                args = [i for i, j in params]
                fnty = ir.FunctionType(_type, args)
                func = ir.Function(self.module, fnty, name=name)
                _type2 = self.symbol_table.getType(name)
                self.symbol_table.insert(name, btype=_type2, value=func)
                return

            _type2 = self.symbol_table.getType(name)
            if _type2[0] == self.ARRAY_TYPE:
                # 数组类型
                length = _type2[1]
                temp = self.builder.alloca(_type, size=length, name=name)
                self.symbol_table.insert(name, btype=_type2, value=temp)
            else:
                # 普通变量
                temp = self.builder.alloca(_type, size=1, name=name)
                if init_val:
                    self.builder.store(init_val, temp)
                # 保存指针
                self.symbol_table.insert(name, btype=_type2, value=temp)



        # rtn_ = self.visit(ctx.initDeclaratorList())
        # len_ = len(rtn_)
        # # 根据返回值长度，判断是否有赋值语句，还是仅仅是声明变量
        # if len_ == 2:
        #     name_, val_ = rtn_[0], rtn_[1]
        #     new_int_ = self.builder.alloca(_type, name=name_)
        #     self.builder.store(_type(val_), new_int_)
        # elif len_ == 1:
        #     name_ = rtn_
        #     new_int_ = self.builder.alloca(_type, name=name_)
        # # return ''

    def visitAssignmentExpression(self, ctx: CParser.AssignmentExpressionContext):
        """
        assignmentExpression
            :   conditionalExpression
            |   unaryExpression assignmentOperator assignmentExpression
        :param ctx:
        :return: 表达式的值，变量本身
        """
        print("assignment",ctx.getText())
        print(ctx.children)
        if ctx.conditionalExpression():
            return self.visit(ctx.conditionalExpression())

    def visitCastExpression(self, ctx:CParser.CastExpressionContext):
        val = self.visit(ctx.unaryExpression())
        if val.type.is_pointer:
            val = self.builder.load(val)
        return val


    def visitMultiplicativeExpression(self, ctx:CParser.MultiplicativeExpressionContext):
        _cast = self.visit(ctx.castExpression())
        if ctx.multiplicativeExpression():
            _mul = self.visit(ctx.multiplicativeExpression())
            if ctx.Star():
                return self.builder.mul(_mul, _cast)
            elif ctx.Div():
                return self.builder.sdiv(_mul, _cast)
            elif ctx.Mod():
                return self.builder.srem(_mul, _cast)
        else:
            return _cast

    def visitAdditiveExpression(self, ctx:CParser.AdditiveExpressionContext):
        _mul = self.visit(ctx.multiplicativeExpression())
        if ctx.additiveExpression():
            _add = self.visit(ctx.additiveExpression())

            if ctx.Plus():
                return self.builder.add(_add, _mul)
            elif ctx.Minus():
                return self.builder.sub(_add, _mul)

        else:
            return _mul

    def visitConditionalExpression(self, ctx:CParser.ConditionalExpressionContext):
        """
        conditionalExpression
            :   logicalOrExpression ('?' expression ':' conditionalExpression)?
        :param ctx:
        :return:表达式的值，变量本身
        """
        print("conditional expression", ctx.children)
        print("expression length", len(ctx.children))
        if len(ctx.children) == 1:
            # 如果没有('?' expression ':' conditionalExpression)?部分
            return self.visit(ctx.logicalOrExpression())
        # cond_val, _ = self.visit(ctx.logicalOrExpression())
        # converted_cond_val = TinyCTypes.cast_type(self.builder, target_type=TinyCTypes.bool, value=cond_val, ctx=ctx)
        # # TODO type cast
        # true_val, _ = self.visit(ctx.expression())
        # false_val, _ = self.visit(ctx.conditionalExpression())
        # ret_pointer = self.builder.alloca(true_val.type)
        # with self.builder.if_else(converted_cond_val) as (then, otherwise):
        #     with then:
        #         self.builder.store(true_val, ret_pointer)
        #     with otherwise:
        #         self.builder.store(false_val, ret_pointer)
        # ret_val = self.builder.load(ret_pointer)
        # return ret_val, None

    def visitLogicalAndExpression(self, ctx: CParser.LogicalAndExpressionContext):
        """
        logicalAndExpression
            :   inclusiveOrExpression
            |   logicalAndExpression '&&' inclusiveOrExpression
            ;
        """
        print("logicalandexpression",ctx.getText())
        if ctx.logicalAndExpression():
            # 如果有多个'与'语句
            lhs, _ = self.visit(ctx.logicalOrExpression())
            result = self.builder.alloca(self.BOOL_TYPE)
            with self.builder.if_else(lhs) as (then, otherwise):
                with then:
                    self.builder.store(self.BOOL_TYPE(1), result)
                with otherwise:
                    rhs, rhs_ptr = self.visit(ctx.logicalAndExpression())
                    self.builder.store(rhs, result)
            return self.builder.load(result), None
        else:
            print(ctx.children)
            return self.visit(ctx.inclusiveOrExpression())

    def visitInclusiveOrExpression(self, ctx:CParser.InclusiveOrExpressionContext):
        """
        inclusiveOrExpression
            :   exclusiveOrExpression
            |   inclusiveOrExpression '|' exclusiveOrExpression
            ;
        :param ctx:
        :return:
        """
        print("inclusiveorexpression",ctx.getText())
        if ctx.inclusiveOrExpression():
            # 上述第二种情况
            return self.visit(ctx.inclusiveOrExpression())
        else:
            return self.visit(ctx.exclusiveOrExpression())

    def visitExclusiveOrExpression(self, ctx:CParser.ExclusiveOrExpressionContext):
        """
        exclusiveOrExpression
            :   andExpression
            |   exclusiveOrExpression '^' andExpression
            ;
        :param ctx:
        :return:
        """
        print("exclusiveorexpression",ctx.getText())
        if ctx.exclusiveOrExpression():
            # 上述第二种情况
            return self.visit(ctx.exclusiveOrExpression())
        else:
            return self.visit(ctx.andExpression())

    def visitAndExpression(self, ctx:CParser.AndExpressionContext):
        """
        andExpression
            :   equalityExpression
            |   andExpression '&' equalityExpression
            ;
        :param ctx:
        :return:
        """
        print("andexpression", ctx.getText())
        if ctx.andExpression():
            # 上述第二种情况
            return self.visit(ctx.andExpression())
        else:
            return self.visit(ctx.equalityExpression())

    def visitLogicalOrExpression(self, ctx: CParser.LogicalOrExpressionContext):
        """
        logicalOrExpression
            :   logicalAndExpression
            |   logicalOrExpression '||' logicalAndExpression
            ;
        """
        print('logicalorexpression',ctx.getText())
        print(ctx.children)
        if ctx.logicalOrExpression():
            # 如果有多个'或'语句
            lhs, _ = self.visit(ctx.logicalOrExpression())
            result = self.builder.alloca(self.BOOL_TYPE)
            # 如果第一个logicalandexpression返回否才继续，否则直接返回真
            with self.builder.if_else(lhs) as (then, otherwise):
                with then:
                    self.builder.store(self.BOOL_TYPE(1), result)
                with otherwise:
                    rhs, rhs_ptr = self.visit(ctx.logicalAndExpression())
                    self.builder.store(rhs, result)
            return self.builder.load(result), None
        else:
            print("no")
            return self.visit(ctx.logicalAndExpression())

    def visitEqualityExpression(self, ctx: CParser.EqualityExpressionContext):
        """
        equalityExpression
            :   relationalExpression
            |   equalityExpression '==' relationalExpression
            |   equalityExpression '!=' relationalExpression
            ;
        :param ctx:
        :return:
        """
        print("equalityexprssion",ctx.getText())
        print(ctx.children)
        if len(ctx.children) == 1:
            return self.visit(ctx.relationalExpression())
        else:
            op = ctx.children[1].getText()
            print("op",op)
            # rhs=ir.Constant(self.INT_TYPE,ctx.children[2].getText())
            # lhs=self.builder.alloca(self.INT_TYPE)
            # self.builder.store(self.INT_TYPE(33),lhs)
            lhs = self.visit(ctx.equalityExpression())
            rhs=self.visit(ctx.relationalExpression())
            return self.builder.icmp_signed(cmpop=op, lhs=lhs, rhs=rhs), None

    def visitRelationalExpression(self, ctx: CParser.RelationalExpressionContext):
        """
        relationalExpression
            :   shiftExpression
            |   relationalExpression '<' shiftExpression
            |   relationalExpression '>' shiftExpression
            |   relationalExpression '<=' shiftExpression
            |   relationalExpression '>=' shiftExpression
            ;
        :param ctx:
        :return:
        """
        # rhs, rhs_ptr = self.visit(ctx.children[-1])
        if len(ctx.children) == 1:
            return self.visit(ctx.shiftExpression())
        else:
            lhs, _ = self.visit(ctx.relationalExpression())
            rhs, _ = self.visit(ctx.shiftExpression())
            op = ctx.children[1].getText()
            converted_target = lhs.type
            if rhs.type == self.INT_TYPE or rhs.type==self.CHAR_TYPE:
                return self.builder.icmp_signed(cmpop=op, lhs=lhs, rhs=rhs), None
            elif rhs.type==self.FLOAT_TYPE:
                return self.builder.fcmp_signed(cmpop=op, lhs=lhs, rhs=rhs), None
            else:
                print("unknown type")

    def visitShiftExpression(self, ctx:CParser.ShiftExpressionContext):
        """
        shiftExpression
            :   additiveExpression
            |   shiftExpression '<<' additiveExpression
            |   shiftExpression '>>' additiveExpression
            ;
        :param ctx:
        :return:
        """
        if len(ctx.children) == 1:
            return self.visit(ctx.additiveExpression())
        else:
            print("you can't do that")


    def visitUnaryExpression(self, ctx:CParser.UnaryExpressionContext):
        _str = ctx.getText()
        if re.match(r'^([\+-])?\d+$', _str):
            val = int(_str)
            return ir.Constant(self.INT_TYPE, val)
        elif re.match(r'^([\+-])?\d*.\d+$', _str):
            val = float(_str)
            return ir.Constant(self.FLOAT_TYPE, val)
        else:
            val = self.symbol_table.getValue(_str)
            return val

    # def visitPostfixExpression(self, ctx: CParser.PostfixExpressionContext):
    #     if ctx.primaryExpression():
    #         return self.visit(ctx.primaryExpression())
    #     if ctx.children[1].getText() == '[':
    #         return f'{self.visit(ctx.postfixExpression())}[{self.visit(ctx.expression())}]'
    #     # function call
    #     functionName = ctx.postfixExpression().getText()
    #     if functionName == 'strlen':
    #         return f'{self.visit(ctx.expression())}.length'
    #     args = ctx.expression()
    #     if args:
    #         args = args.assignmentExpression()
    #         args = [self.visit(x) for x in args]
    #     if functionName == 'printf':
    #         # printf doesn't append a newline but console
    #         if args[0].endswith('\\n\"'):
    #             args[0] = args[0][:-3] + '"'
    #         return f'console.log({", ".join(args)})'
    #     if ctx.expression():
    #         return f'{ctx.postfixExpression().getText()}({self.visit(ctx.expression())})'
    #     return f'{ctx.postfixExpression().getText()}()'

    def visitPrimaryExpression(self, ctx: CParser.PrimaryExpressionContext):
        return ctx.children[0].getText()

    # def visitExpression(self, ctx: CParser.ExpressionContext):
    #     return ', '.join([self.visit(x) for x in ctx.assignmentExpression()])

    def visitCompoundStatement(self, ctx):
        for i in ctx.children[1:-1]:
            self.visit(i)
        # return '\n{\n' + addIndentation('\n'.join([self.visit(i) for i in ctx.children[1:-1]])) + '\n}'

    def visitBlockItem(self, ctx):
        if ctx.statement():
            return self.visit(ctx.statement())
        return self.visit(ctx.declaration())

    def visitInitDeclaratorList(self, ctx):
        declarator_list = []
        declarator_list.append(self.visit(ctx.initDeclarator()))
        if ctx.initDeclaratorList():
            declarator_list += self.visit(ctx.initDeclaratorList())
        return declarator_list

        # print("text", ctx.getText())
        # return self.visit(ctx.initDeclarator())

    def visitInitDeclarator(self, ctx):
        if ctx.initializer():
            declarator = (self.visit(ctx.declarator()), self.visit(ctx.initializer()))
        else:
            declarator = (self.visit(ctx.declarator()), None)
        return declarator

        # if ctx.initializer():
        #     # 如果有赋值语句，就返回值和变量名；否则只返回变量名
        #     return ctx.declarator().getText(), ctx.initializer().getText()
        # return ctx.declarator().getText()

    def visitInitializer(self, ctx):
        if ctx.assignmentExpression():
            return self.visit(ctx.assignmentExpression())
        if ctx.initializerList():
            return '[' + self.visit(ctx.initializerList()) + ']'
        return '[]'

    def visitJumpStatement(self, ctx):
        if ctx.Return():
            if ctx.expression():
                _value = self.visit(ctx.expression())
                self.builder.ret(_value)
            else:
                self.builder.ret_void()

        elif ctx.Continue():
            pass
        elif ctx.Break():
            pass

    def visitIterationStatement(self, ctx:CParser.IterationStatementContext):
        if ctx.While():
            block_name = self.builder.block.name
            loop_block = self.builder.append_basic_block(name='{}_loop'.format(block_name))
            # continue_block = self.builder.append_basic_block(name='{}_comtinue'.format(block_name))
            end_block = self.builder.append_basic_block(name='{}_continue'.format(block_name))
            self.builder.position_at_start(loop_block)
            expression = self.visit(ctx.expression())
            with self.builder.if_else(expression) as (then, otherwise):
                with then:
                    self.builder.branch(loop_block)
                with otherwise:
                    self.builder.branch(end_block)
            self.builder.position_at_start(end_block)
        elif ctx.Do():
            pass
        elif ctx.For():
            pass

    # def visitStatement(self, ctx):
    #     if ctx.compoundStatement():
    #         return self.visit(ctx.compoundStatement())
    #     if isinstance(ctx.children[0], CParser.ExpressionContext):
    #         return self.visit(ctx.children[0]) + ';'
    #     txt = ctx.children[0].getText()
    #     if txt == 'if':
    #         if_statements = f'if({self.visit(ctx.expression())})' + \
    #             self.visit(ctx.statement(0))
    #         else_statement = ''
    #         if len(ctx.children) > 5:
    #             else_statement = '\nelse' + self.visit(ctx.statement(1))
    #         return if_statements + else_statement
    #     if txt == 'while':
    #         return f'while({self.visit(ctx.expression())})' + self.visit(ctx.statement(0))
    #     if txt == 'for':
    #         forDeclaration = ctx.forDeclaration()
    #         forDeclaration = '' if not forDeclaration else self.visit(
    #             forDeclaration)
    #         forExpression_0 = ctx.forExpression(0)
    #         forExpression_0 = '' if not forExpression_0 else self.visit(
    #             forExpression_0)
    #         forExpression_1 = ctx.forExpression(1)
    #         forExpression_1 = '' if not forExpression_1 else self.visit(
    #             forExpression_1)
    #         return f'for ({forDeclaration}; {forExpression_0}; {forExpression_1})' + self.visit(ctx.statement(0))
    #     if txt == 'return':
    #         expression = ''
    #         if ctx.expression():
    #             expression = self.visit(ctx.expression())
    #         return f'return {expression};'
    #     return ctx.getText()

    def visitSelectionStatement(self, ctx:CParser.SelectionStatementContext):
        """
        selectionStatement
            :   'if' '(' expression ')' statement ('else' statement)?
            |   'switch' '(' expression ')' statement
            ;
        :param ctx:
        :return:
        """
        print("selection",ctx.children)
        if ctx.children[0].getText() == 'if':
            # print(ctx.statement()[0].getText())
            # print(ctx.statement()[1].getText())
            print(ctx.expression().getText())
            expr_val, _ = self.visit(ctx.expression())
            print("expression result:", expr_val, _)
            branches = ctx.statement()
            if len(branches) == 2:  # 存在else if/else语句
                with self.builder.if_else(expr_val) as (then, otherwise):
                    with then:
                        self.symbol_table = createTable(self.symbol_table)
                        self.visit(branches[0])
                        self.symbol_table = self.symbol_table.getFather()
                    with otherwise:
                        self.symbol_table = createTable(self.symbol_table)
                        self.visit(branches[1])
                        self.symbol_table = self.symbol_table.getFather()
            else:  # 只有if分支
                with self.builder.if_then(expr_val):
                    self.symbol_table = createTable(self.symbol_table)
                    self.visit(branches[0])
                    self.symbol_table = self.symbol_table.getFather()
        # if ctx.children[0].getText() == 'if':
        #     cond_val, _ = self.visit(ctx.expression())
        #     converted_cond_val = TinyCTypes.cast_type(self.builder, target_type=TinyCTypes.bool, value=cond_val, ctx=ctx)
        #     statements = ctx.statement()
        #     self.symbol_table.enter_scope()
        #     if len(statements) == 2:  # 存在else分支
        #         with self.builder.if_else(converted_cond_val) as (then, otherwise):
        #             with then:
        #                 self.visit(statements[0])
        #             with otherwise:
        #                 self.visit(statements[1])
        #     else:  # 只有if分支
        #         with self.builder.if_then(converted_cond_val):
        #             self.visit(statements[0])
        #     self.symbol_table.exit_scope()
        # else:
        #     name_prefix = self.builder.block.name
        #     start_block = self.builder.block
        #     end_block = self.builder.append_basic_block(name=name_prefix + '.end_switch')
        #     old_context = self.switch_context
        #     old_break = self.break_block
        #     self.break_block = end_block
        #     cond_val, _ = self.visit(ctx.expression())
        #     self.switch_context = [[], None, name_prefix + '.case.']
        #     self.visit(ctx.statement(0))
        #     try:
        #         self.builder.branch(end_block)
        #     except AssertionError:
        #         # 最后一个标签里有break或return语句，不用跳转
        #         pass
        #     label_blocks = []
        #     for i in range(len(self.switch_context[0])):
        #         label_blocks.append(self.builder.append_basic_block(name=name_prefix + '.label.' + str(i)))
        #     self.builder.position_at_end(start_block)
        #     self.builder.branch(label_blocks[0])
        #     for i, (label, _block) in enumerate(self.switch_context[0]):
        #         self.builder.position_at_end(label_blocks[i])
        #         if isinstance(label, str):
        #             self.builder.branch(_block)
        #         else:
        #             constant, _ = self.visit(label)
        #             condition = self.builder.icmp_signed(cmpop='==', lhs=cond_val, rhs=constant)
        #             if i == len(self.switch_context[0]) - 1:
        #                 false_block = end_block
        #             else:
        #                 false_block = label_blocks[i + 1]
        #             self.builder.cbranch(condition, _block, false_block)
        #     self.builder.position_at_start(end_block)
        #     self.switch_context = old_context
        #     self.break_block = old_break

    def visitForDeclaration(self, ctx: CParser.ForDeclarationContext):
        return self.visit(ctx.typeSpecifier()) + ' ' + self.visit(ctx.initDeclaratorList())

    def visitTerminal(self, node):
        return node.getText()

    def visitInitializerList(self, ctx: CParser.InitializerListContext):
        return ', '.join([self.visit(x) for x in ctx.initializer()])

    def visitParameterTypeList(self, ctx: CParser.ParameterTypeListContext):
        """
            parameterTypeList
                :   parameterList
                |   parameterList ',' '...'
                ;
            :param ctx:
            :return: 参数列表, true/false
        """
        if ctx.parameterList():
            return self.visit(ctx.parameterList())
        # if len(ctx.children) == 1:
        #     return self.visit(ctx.parameterList()), False
        # else:
        #     return self.visit(ctx.parameterList()), True

    def visitParameterList(self, ctx: CParser.ParameterListContext):
        """
            parameterList
                :   parameterDeclaration
                |   parameterList ',' parameterDeclaration
                ;
            :param ctx:
            :return: 返回变量名字列表arg_names和变量类型列表arg_types
        """
        if ctx.parameterList():
            _param_list = self.visit(ctx.parameterList())
        else:
            _param_list = []
        _param_decl = self.visit(ctx.parameterDeclaration())
        _param_list.append(_param_decl)
        return _param_list

        # if len(ctx.children) == 1:
        #     arg_list = []
        # else:
        #     arg_list = self.visit(ctx.parameterList())
        # item = self.visit(ctx.parameterDeclaration())
        # arg_list.append(item)
        # return arg_list

    def visitParameterDeclaration(self, ctx: CParser.ParameterDeclarationContext):
        _type = self.visit(ctx.declarationSpecifiers())
        _name = self.visit(ctx.declarator())
        # _type.name = _name
        return _type, _name

    def output(self):
        """返回代码"""
        return repr(self.module)


def main(argv):
    input = FileStream('test.c' if len(argv) <= 1 else argv[1])
    lexer = CLexer(input)
    stream = CommonTokenStream(lexer)
    parser = CParser(stream)
    tree = parser.compilationUnit()
    _visitor = ToJSVisitor()
    _visitor.visit(tree)

    with open('test.ll' if len(argv) <= 2 else argv[2], 'w', encoding='utf-8') as f:
        f.write(_visitor.output())
    print(_visitor.output())


if __name__ == '__main__':
    main(['main', 'test.c'])
