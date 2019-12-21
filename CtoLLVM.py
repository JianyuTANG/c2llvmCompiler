import sys
from antlr4 import *
from parser_.CLexer import CLexer
from parser_.CParser import CParser
from parser_.CVisitor import CVisitor
from llvmlite import ir
from SymbolTable import SymbolTable, ArrayType, BasicType


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
        assert ctx.declarationList() == None
        _type = self.visit(ctx.declarationSpecifiers())
        # self.visit(ctx.declarator())
        name, params = self.visit(ctx.declarator())
        args = [i for i, j in params]
        fnty = ir.FunctionType(_type, args)
        func = ir.Function(self.module, fnty, name=name)
        block = func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)
        self.visit(ctx.compoundStatement())
        # ans = 'function'
        # ans += ' ' + self.visit(ctx.declarator())
        # ans += ' ' + self.visit(ctx.compoundStatement())
        # return ans

    # def visitDeclarationSpecifiers(self, ctx):
    #     if ctx.CONST():
    #         return 'const'
    #     return 'let'

    def visitDeclarator(self, ctx: CParser.DeclaratorContext):
        # 只考虑后继为 directDeclarator 的情况
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
            params = self.visit(ctx.parameterTypeList())
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
            _type2 = self.symbol_table.getType(name)
            if _type2[0] == self.ARRAY_TYPE:
                # 数组类型
                length = _type2[1]
            else:
                # 普通变量
                length = 1
            temp = self.builder.alloca(_type, size=length, name=name)
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
        if ctx.logicalAndExpression():
            return self.visit(ctx.logicalAndExpression())
        if ctx.logicalOrExpression():
            return self.visit(ctx.logicalOrExpression())
        else:
            return self.visit(ctx.unaryExpression()) + ' = ' + self.visit(ctx.assignmentExpression())

    def visitLogicalAndExpression(self, ctx: CParser.LogicalAndExpressionContext):
        if ctx.logicalAndExpression():
            return self.visit(ctx.logicalAndExpression()) + ' && ' + self.visit(ctx.equalityExpression())
        else:
            return self.visit(ctx.equalityExpression())

    def visitLogicalOrExpression(self, ctx: CParser.LogicalOrExpressionContext):
        if ctx.logicalOrExpression():
            return self.visit(ctx.logicalOrExpression()) + ' || ' + self.visit(ctx.equalityExpression())
        else:
            return self.visit(ctx.equalityExpression())

    def visitEqualityExpression(self, ctx: CParser.EqualityExpressionContext):
        if len(ctx.children) == 1:
            return self.visit(ctx.relationalExpression())
        else:
            op = ctx.children[1].getText()
            if op == '==':
                op = '==='
            if op == '!=':
                op = '!=='
            return self.visit(ctx.equalityExpression()) + f' {op} ' + \
                self.visit(ctx.relationalExpression())

    def visitRelationalExpression(self, ctx: CParser.RelationalExpressionContext):
        if len(ctx.children) > 1:
            return self.visit(ctx.castExpression(0)) + ' ' + ctx.children[1].getText() + ' ' + self.visit(ctx.castExpression(1))
        else:
            return self.visit(ctx.castExpression(0))

    def visitCastExpression(self, ctx: CParser.CastExpressionContext):
        if ctx.unaryExpression():
            return self.visit(ctx.unaryExpression())
        else:
            return ' '.join([self.visit(x) for x in ctx.children])

    def visitUnaryExpression(self, ctx: CParser.UnaryExpressionContext):
        if len(ctx.children) > 1:
            return ctx.children[0].getText() + ' ' + self.visit(ctx.postfixExpression())
        else:
            return self.visit(ctx.postfixExpression())

    def visitPostfixExpression(self, ctx: CParser.PostfixExpressionContext):
        if ctx.primaryExpression():
            return self.visit(ctx.primaryExpression())
        if ctx.children[1].getText() == '[':
            return f'{self.visit(ctx.postfixExpression())}[{self.visit(ctx.expression())}]'
        # function call
        functionName = ctx.postfixExpression().getText()
        if functionName == 'strlen':
            return f'{self.visit(ctx.expression())}.length'
        args = ctx.expression()
        if args:
            args = args.assignmentExpression()
            args = [self.visit(x) for x in args]
        if functionName == 'printf':
            # printf doesn't append a newline but console
            if args[0].endswith('\\n\"'):
                args[0] = args[0][:-3] + '"'
            return f'console.log({", ".join(args)})'
        if ctx.expression():
            return f'{ctx.postfixExpression().getText()}({self.visit(ctx.expression())})'
        return f'{ctx.postfixExpression().getText()}()'

    def visitPrimaryExpression(self, ctx: CParser.PrimaryExpressionContext):
        return ctx.children[0].getText()

    def visitExpression(self, ctx: CParser.ExpressionContext):
        return ', '.join([self.visit(x) for x in ctx.assignmentExpression()])

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

    def visitStatement(self, ctx):
        if ctx.compoundStatement():
            return self.visit(ctx.compoundStatement())
        if isinstance(ctx.children[0], CParser.ExpressionContext):
            return self.visit(ctx.children[0]) + ';'
        txt = ctx.children[0].getText()
        if txt == 'if':
            if_statements = f'if({self.visit(ctx.expression())})' + \
                self.visit(ctx.statement(0))
            else_statement = ''
            if len(ctx.children) > 5:
                else_statement = '\nelse' + self.visit(ctx.statement(1))
            return if_statements + else_statement
        if txt == 'while':
            return f'while({self.visit(ctx.expression())})' + self.visit(ctx.statement(0))
        if txt == 'for':
            forDeclaration = ctx.forDeclaration()
            forDeclaration = '' if not forDeclaration else self.visit(
                forDeclaration)
            forExpression_0 = ctx.forExpression(0)
            forExpression_0 = '' if not forExpression_0 else self.visit(
                forExpression_0)
            forExpression_1 = ctx.forExpression(1)
            forExpression_1 = '' if not forExpression_1 else self.visit(
                forExpression_1)
            return f'for ({forDeclaration}; {forExpression_0}; {forExpression_1})' + self.visit(ctx.statement(0))
        if txt == 'return':
            expression = ''
            if ctx.expression():
                expression = self.visit(ctx.expression())
            return f'return {expression};'
        return ctx.getText()

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
