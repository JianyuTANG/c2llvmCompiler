import sys
from antlr4 import *
from parser_.CLexer import CLexer
from parser_.CParser import CParser
from parser_.CVisitor import CVisitor
from llvmlite import ir
import re
from SymbolTable import *
from StructTable import *


def addIndentation(a, num=2):
    return '\n'.join([' ' * num + i for i in a.split('\n')])


def getSize(_type):
    pass


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
        self.builder = None
        self.symbol_table = SymbolTable(None)
        self.lst_continue = None
        self.lst_break = None
        self.func_table = FuncTable()
        self.struct_table = StructTable()
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
        self.symbol_table.insert(name, value=func)
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

    # def visitFunctionDefinitionOrDeclaration(self, ctx: CParser.FunctionDefinitionContext):
    #     if ctx.declarationList():
    #         return f'{ctx.declarator().directDeclarator().Identifier().getText()}({self.visit(ctx.declarationList())})'
    #     return f'{ctx.declarator().directDeclarator().Identifier().getText()}()'

    def visitTypeSpecifier(self, ctx: CParser.TypeSpecifierContext):
        if ctx.pointer():
            _type = self.visit(ctx.typeSpecifier())
            return ir.PointerType(_type)
        else:
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
                fnty = ir.FunctionType(_type, args,  var_arg=True)
                func = ir.Function(self.module, fnty, name=name)
                _type2 = self.symbol_table.getType(name)
                self.symbol_table.insert(name, btype=_type2, value=func)
                continue

            _type2 = self.symbol_table.getType(name)
            if _type2[0] == self.ARRAY_TYPE:
                # 数组类型
                length = _type2[1]
                arr_type = ir.ArrayType(_type, length.constant)
                if self.builder:
                    temp = self.builder.alloca(arr_type, name=name)
                    if init_val:
                        # 有初值
                        l = len(init_val)
                        if l > length.constant:
                            # 数组过大
                            return
                        for i in range(l):
                            indices = [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), i)]
                            ptr = self.builder.gep(ptr=temp, indices=indices)
                            self.builder.store(init_val[i], ptr)
                        temp = self.builder.bitcast(temp, ir.PointerType(_type))
                        temp_ptr = self.builder.alloca(temp.type)
                        self.builder.store(temp, temp_ptr)
                        temp = temp_ptr
                else:
                    temp = ir.GlobalValue(self.module, arr_type, name=name)
                # 保存指针
                self.symbol_table.insert(name, btype=_type2, value=temp)

            else:
                # 普通变量
                if self.builder:
                    temp = self.builder.alloca(_type, size=1, name=name)
                    if init_val:
                        # if _type.is_pointer and _type.pointee == self.CHAR_TYPE:
                        #     # 字符串指针变量
                        #     ptr = self.builder.alloca(init_val.type)
                        #     self.builder.store(init_val, ptr)
                        #     ptr = self.builder.bitcast(ptr, _type)
                        #     self.builder.store(ptr, temp)
                        # else:
                        #     # 其他变量
                        self.builder.store(init_val, temp)
                else:
                    temp = ir.GlobalValue(self.module, _type, name=name)
                    # if init_val:
                    #     temp.store(value=init_val, ptr=temp)

                # 保存指针
                self.symbol_table.insert(name, btype=_type2, value=temp)

    def visitAssignmentExpression(self, ctx: CParser.AssignmentExpressionContext):
        """
        assignmentExpression
            :   conditionalExpression
            |   unaryExpression assignmentOperator assignmentExpression
        :param ctx:
        :return: 表达式的值，变量本身
        """
        print("assignment expression:",ctx.getText())
        print(ctx.children)
        if ctx.conditionalExpression():
            print("into conditional")
            return self.visit(ctx.conditionalExpression())
        elif ctx.unaryExpression():
            lhs, pt=self.visit(ctx.unaryExpression())
            if not pt:
                raise Exception()
            op_=self.visit(ctx.assignmentOperator())
            value_=self.visit(ctx.assignmentExpression())
            if op_=='=':
                return self.builder.store(value_,lhs)
            elif op_=='+=':
                old_value_=self.builder.load(lhs)
                new_value_=self.builder.add(value_,old_value_)
                return self.builder.store(new_value_,lhs)
            elif op_=='-=':
                old_value_=self.builder.load(lhs)
                new_value_=self.builder.sub(old_value_,value_)
                return self.builder.store(new_value_,lhs)
            elif op_=='*=':
                old_value_=self.builder.load(lhs)
                new_value_=self.builder.mul(old_value_,value_)
                return self.builder.store(new_value_,lhs)
            elif op_=='/=':
                old_value_=self.builder.load(lhs)
                new_value_=self.builder.sdiv(old_value_,value_)
                return self.builder.store(new_value_,lhs)
            elif op_=='%=':
                old_value_=self.builder.load(lhs)
                new_value_=self.builder.srem(old_value_,value_)
                return self.builder.store(new_value_,lhs)
            else:
                print("unknown assignment operator")


    def visitAssignmentOperator(self, ctx:CParser.AssignmentOperatorContext):
        """
        assignmentOperator
            :   '=' | '*=' | '/=' | '%=' | '+=' | '-=' | '<<=' | '>>=' | '&=' | '^=' | '|='
            ;
        :param ctx:
        :return:
        """
        print("assignment operator:",ctx.getText())
        return (ctx.getText())


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
            lhs = self.visit(ctx.logicalOrExpression())
            result = self.builder.alloca(self.BOOL_TYPE)
            with self.builder.if_else(lhs) as (then, otherwise):
                with then:
                    self.builder.store(self.BOOL_TYPE(1), result)
                with otherwise:
                    rhs = self.visit(ctx.logicalAndExpression())
                    self.builder.store(rhs, result)
            return self.builder.load(result)
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
            lhs= self.visit(ctx.logicalOrExpression())
            result = self.builder.alloca(self.BOOL_TYPE)
            # 如果第一个logicalandexpression返回否才继续，否则直接返回真
            with self.builder.if_else(lhs) as (then, otherwise):
                with then:
                    self.builder.store(self.BOOL_TYPE(1), result)
                with otherwise:
                    rhs= self.visit(ctx.logicalAndExpression())
                    self.builder.store(rhs, result)
            return self.builder.load(result)
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
        print("equalityexprssion", ctx.getText())
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
            return self.builder.icmp_signed(cmpop=op, lhs=lhs, rhs=rhs)

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
        print("relational expression",ctx.getText())
        if len(ctx.children) == 1:
            return self.visit(ctx.shiftExpression())
        else:
            lhs= self.visit(ctx.relationalExpression())
            print("bbb")
            rhs = self.visit(ctx.shiftExpression())
            op = ctx.children[1].getText()
            converted_target = lhs.type
            if rhs.type == self.INT_TYPE or rhs.type==self.CHAR_TYPE:
                return self.builder.icmp_signed(cmpop=op, lhs=lhs, rhs=rhs)
            elif rhs.type==self.FLOAT_TYPE:
                return self.builder.fcmp_signed(cmpop=op, lhs=lhs, rhs=rhs)
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


    def visitMultiplicativeExpression(self, ctx:CParser.MultiplicativeExpressionContext):
        _cast, _ = self.visit(ctx.castExpression())
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

    def visitCastExpression(self, ctx:CParser.CastExpressionContext):
        if ctx.unaryExpression():
            val, pt = self.visit(ctx.unaryExpression())
            if pt:
                pt = val
                val = self.builder.load(val)
            return val, pt

        if ctx.typeName():
            _target_type = self.visit(ctx.typeName())
            val, pt = self.visit(ctx.castExpression())
            val = self.builder.bitcast(val, _target_type)
            return val, pt


    def visitUnaryExpression(self, ctx:CParser.UnaryExpressionContext):
        if ctx.postfixExpression():
            return self.visit(ctx.postfixExpression())

        if ctx.unaryOperator():
            val, pt = self.visit(ctx.castExpression())
            op = self.visit(ctx.unaryOperator())
            if op == '-':
                return self.builder.neg(val), False
            elif op == '&':
                if pt:
                    return pt, False
                else:
                    raise Exception()
            elif op == '*':
                pt = val
                val = self.builder.load(pt)
                return val, pt

    def visitPostfixExpression(self, ctx: CParser.PostfixExpressionContext):
        """
        postfixExpression
            :   primaryExpression
            |   postfixExpression '[' expression ']'
            |   postfixExpression '(' argumentExpressionList? ')'
            |   postfixExpression '.' Identifier
            |   postfixExpression '->' Identifier
            |   postfixExpression '++'
            |   postfixExpression '--'
            |   '(' typeName ')' '{' initializerList '}'
            |   '(' typeName ')' '{' initializerList ',' '}'
            |   '__extension__' '(' typeName ')' '{' initializerList '}'
            |   '__extension__' '(' typeName ')' '{' initializerList ',' '}'
            ;
        :param ctx:
        :return:
        """
        print("postfix expression:", ctx.children)
        if ctx.primaryExpression():
            return self.visit(ctx.primaryExpression())

        elif ctx.expression():
            # 获取指向指针的指针
            var, pt = self.visit(ctx.postfixExpression())
            if not pt:
                raise Exception()
            # 得到指针的值
            var = self.builder.load(var)
            # 获取指针指向的类型
            value = self.builder.load(var)
            arr_type = ir.PointerType(ir.ArrayType(value.type, 100))
            # 将指针转换为指向数组的指针
            var = self.builder.bitcast(var, arr_type)
            # 获取 index 并构造 indices
            index = self.visit(ctx.expression())
            indices = [ir.Constant(self.INT_TYPE, 0), index]
            # 取值
            ptr = self.builder.gep(ptr=var, indices=indices)
            return ptr, True
        elif ctx.postfixExpression():
            if ctx.children[1].getText()=='(':
                # 表示是一个函数声明
                print(ctx.postfixExpression().getText())
                if ctx.argumentExpressionList():
                    args_ = self.visit(ctx.argumentExpressionList())
                    print(ctx.argumentExpressionList().getText())
                else:
                    args_=[]
                lhs, _=self.visit(ctx.postfixExpression())
                return self.builder.call(lhs, args_), False

    def visitPrimaryExpression(self, ctx: CParser.PrimaryExpressionContext):
        """
        primaryExpression
            :   Identifier
            |   Constant
            |   StringLiteral+
            |   '(' expression ')'
            |   genericSelection
            |   '__extension__'? '(' compoundStatement ')' // Blocks (GCC extension)
            |   '__builtin_va_arg' '(' unaryExpression ',' typeName ')'
            |   '__builtin_offsetof' '(' typeName ',' unaryExpression ')'
            ;
        :param ctx:
        :return:
        """
        _str = ctx.getText()
        print("primary expression: ",_str)
        print(ctx.children)
        if ctx.Identifier():
            print(ctx.Identifier().getText())
            print("symbol table",self.symbol_table.value_list)
            rhs=self.symbol_table.getValue(ctx.Identifier().getText())
            print(rhs)
            return rhs, True
        if ctx.Constant():
            _str = ctx.Constant().getText()
            val = eval(_str)
            if val.__class__ == int:
                return ir.Constant(self.INT_TYPE, val), False
            elif val.__class__ == float:
                return ir.Constant(self.FLOAT_TYPE, val), False
            elif val.__class__ == str:
                val = ord(val)
                return ir.Constant(self.CHAR_TYPE, val), False
            else:
                raise Exception()
        elif ctx.StringLiteral():
            _str = eval(ctx.StringLiteral()[0].getText())
            # byte = _str.encode('ascii') + b'\0'
            # length = len(_str) + 1
            # arr_type = ir.ArrayType(self.CHAR_TYPE, length)
            _str_array = [ir.Constant(self.CHAR_TYPE, ord(i)) for i in _str] + [ir.Constant(self.CHAR_TYPE, 0)]
            temp = ir.Constant.literal_array(_str_array)
            arr_type = ir.ArrayType(self.CHAR_TYPE, len(_str_array))
            ptr = self.builder.alloca(arr_type)
            self.builder.store(temp, ptr)
            ptr = self.builder.bitcast(ptr, ir.PointerType(self.CHAR_TYPE))
            # pptr = self.builder.alloca(ptr.type)
            # self.builder.store(ptr, pptr)
            # # temp = self.builder.alloca(arr_type)
            # for seq, val in enumerate(_str):
            #     self.builder.insert_value(temp, val, seq)
            #     # 处理字符串
            return ptr, False
        # else:
        #     # 变量名
        #     val = self.symbol_table.getValue(_str)
        #     val = self.builder.load(val)
        #     return val

    # def visitExpression(self, ctx: CParser.ExpressionContext):
    #     return ', '.join([self.visit(x) for x in ctx.assignmentExpression()])

    def visitArgumentExpressionList(self, ctx:CParser.ArgumentExpressionListContext):
        if not ctx.argumentExpressionList():
            return [self.visit(ctx.assignmentExpression())]
        
        _args = self.visit(ctx.argumentExpressionList())
        _args.append(self.visit(ctx.assignmentExpression()))
        return _args


    def visitCompoundStatement(self, ctx):
        for i in ctx.children:
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
        elif ctx.initializerList():
            return self.visit(ctx.initializerList())

    def visitJumpStatement(self, ctx):
        if ctx.Return():
            if ctx.expression():
                _value = self.visit(ctx.expression())
                self.builder.ret(_value)
            else:
                self.builder.ret_void()

        elif ctx.Continue():
            if self.lst_continue:
                self.builder.branch(self.lst_continue)
            else:
                raise Exception()
        elif ctx.Break():
            if self.lst_break:
                self.builder.branch(self.lst_break)
            else:
                raise Exception()

    def visitIterationStatement(self, ctx:CParser.IterationStatementContext):
        if ctx.While():
            # block_name = self.builder.block.name
            self.symbol_table = createTable(self.symbol_table)
            init_block = self.builder.append_basic_block()#(name='{}.loop_init'.format(block_name))
            do_block = self.builder.append_basic_block()#(name='{}.loop_do'.format(block_name))
            end_block = self.builder.append_basic_block()#(name='{}.loop_end'.format(block_name))
            lst_continue, lst_break = self.lst_continue, self.lst_break
            self.lst_continue, self.lst_break = init_block, end_block
            self.builder.branch(init_block)
            self.builder.position_at_start(init_block)
            expression = self.visit(ctx.expression())
            self.builder.cbranch(expression, do_block, end_block)
            self.builder.position_at_start(do_block)
            self.visit(ctx.statement())
            self.builder.branch(init_block)
            # with self.builder.if_else(expression) as (then, otherwise):
            #     with then:
            #         self.builder.branch(loop_block)
            #     with otherwise:
            #         self.builder.branch(end_block)
            self.builder.position_at_start(end_block)
            self.lst_continue, self.lst_break = lst_continue, lst_break
            self.symbol_table = self.symbol_table.getFather()
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
        if ctx.If():
            # print(ctx.statement()[0].getText())
            # print(ctx.statement()[1].getText())
            print(ctx.expression().getText())
            expr_val = self.visit(ctx.expression())
            print("expression result:", expr_val)
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
        '''

initializerList
    :   designation? initializer
    |   initializerList ',' designation? initializer
    ;
        不考虑有designation的情况
        :param ctx:
        :return:
        '''
        ans = [self.visit(ctx.initializer())]
        if ctx.initializerList():
            ans = self.visit(ctx.initializerList()) + ans
        return ans

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
