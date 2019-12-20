import sys
from antlr4 import *
from parser_.CLexer import CLexer
from parser_.CParser import CParser
from parser_.CVisitor import CVisitor
import llvmlite.ir as ir


def addIndentation(a, num=2):
    return '\n'.join([' ' * num + i for i in a.split('\n')])


class ToJSVisitor(CVisitor):
    BASE_TYPE = 0
    ARRAY_TYPE = 1
    FUNCTION_TYPE = 2

    def __init__(self):
        # Create some useful types
        double = ir.DoubleType()
        self.fnty = ir.FunctionType(double, (double, double))

        # Create an empty module...
        self.module = ir.Module()
        ir.GlobalVariable(self.module, ir.IntType(32), name="glo")
        # and declare a function named "fpadd" inside it
        self.func = ir.Function(self.module, self.fnty, name="fpadd")
        #ir.GlobalVariable(self.module, ir.IntType(32), name="glo")
        # Now implement the function
        self.block = self.func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(self.block)
        # a, b = self.func.args
        # result = self.builder.fadd(a, b, name="res")
        # self.builder.ret(result)
        # self.builder.alloca(ir.IntType(32),name="aaa")
        # a=self.builder.alloca(ir.IntType(32), name="aab")
        # self.builder.store(ir.IntType(32)(9),a)

    def visitCompilationUnit(self, ctx):
        ans = [self.visit(i) for i in ctx.children[:-1]]
        # ans = [x for x in ans if x]
        return '\n'.join(ans) # + '\nmain();\n'

    def visitFunctionDefinition(self, ctx):
        ans = 'function'
        ans += ' ' + self.visit(ctx.declarator())
        ans += ' ' + self.visit(ctx.compoundStatement())
        return ans

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
        if ctx.getRuleIndex() == CParser.Identifier:
            # Identifier 普通变量名
            return ctx.getText(), self.current_type, []
        elif ctx.children[0].getRuleIndex() == CParser.Identifier:
            if ctx.children[1].getText() == '[':
                # 数组
                name, tp, sz = self.visitDirectDeclarator(ctx.directDeclarator())
                tp = ir.PointerType(tp)
                if ctx.children[2].getText() == ']':
                    # 形如 a[] 实际上是指针
                    return name, tp, sz
                else:
                    try:
                        length = int(ctx.assignmentExpression().getText())
                    except:
                        # ERROR
                        return
                    if length <= 0:
                        # ERROR
                        return
                    sz.append(length)
                    return name, tp, sz
            elif ctx.children[1].getText() == '(':
                # 函数声明
                name, ret_tp, pms = self.visitDirectDeclarator(ctx.directDeclarator())
                ret_tp = ir.FunctionType(ret_tp, pms)
                if ctx.children[2].getText() == ')':
                    # 无参数 形如a()
                    return name, ret_tp, []
                elif ctx.children[2].getRuleIndex() == CParser.parameterTypeList:
                    # 有参数 形如a(int, char, ...)
                    pass
            else:
                # ERROR
                pass
        else:
            # ERROR
            pass

    def visitTypeSpecifier(self, ctx):
        if ctx.CONST():
            return 'const'
        return 'let'

    def visitPureIdentifier(self, ctx:CParser.DeclaratorContext):
        return ctx.directDeclarator().Identifier().getText()

    # def visitArrayIdentifier(self, ctx:CParser.ArrayIdentifierContext):
    #     if ctx.assignmentExpression():
    #         # array definition
    #         length = self.visit(ctx.assignmentExpression())
    #         return f'{ctx.Identifier().getText()} = new Array({length})'
    #     else:
    #         # string definition
    #         return f'{ctx.Identifier().getText()}'

    def visitFunctionDefinitionOrDeclaration(self, ctx:CParser.FunctionDefinitionContext):
        if ctx.declarationList():
            return f'{ctx.declarator().directDeclarator().Identifier().getText()}({self.visit(ctx.declarationList())})'
        return f'{ctx.declarator().directDeclarator().Identifier().getText()}()'

    def visitDeclaration(self, ctx):
        # if isinstance(ctx.initDeclaratorList().initDeclarator(0).declarator(), CParser.FunctionDefinitionOrDeclarationContext):
        #     # there is no function declaration in JS
        #     return
        # _specifier
        _specifier = ctx.declarationSpecifiers().declarationSpecifier()[-1].getText()
        _type = {
            'int':(32, 4),
            'char':(8, 4)
        }.get(_specifier)
        #print(ctx.initDeclaratorList().initDeclarator)
        print("here",ctx.children)
        rtn_ = self.visit(ctx.initDeclaratorList())
        len_=len(rtn_)
        if _specifier=='int':
            # 根据返回值长度，判断是否有赋值语句，还是仅仅是声明变量
            if len_==2:
                name_,val_=rtn_[0],rtn_[1]
                new_int_=self.builder.alloca(ir.IntType(32),name=name_)
                self.builder.store(ir.IntType(32)(val_), new_int_)
            elif len_==1:
                name_= rtn_
                new_int_ = self.builder.alloca(ir.IntType(32), name=name_)
        elif _specifier=='char':
            if len_ == 2:
                name_, val_ = rtn_[0],rtn_[1]
                new_int_ = self.builder.alloca(ir.IntType(8), name=name_)
                self.builder.store(ir.IntType(8)(val_), new_int_)
            elif len_ == 1:
                name_ = rtn_
                new_int_ = self.builder.alloca(ir.IntType(8), name=name_)
        return ''

    def visitAssignmentExpression(self, ctx:CParser.AssignmentExpressionContext):
        if ctx.logicalAndExpression():
            return self.visit(ctx.logicalAndExpression())
        if ctx.logicalOrExpression():
            return self.visit(ctx.logicalOrExpression())
        else:
            return self.visit(ctx.unaryExpression()) + ' = ' + self.visit(ctx.assignmentExpression())

    def visitLogicalAndExpression(self, ctx:CParser.LogicalAndExpressionContext):
        if ctx.logicalAndExpression():
            return self.visit(ctx.logicalAndExpression()) + ' && ' + self.visit(ctx.equalityExpression())
        else:
            return self.visit(ctx.equalityExpression())

    def visitLogicalOrExpression(self, ctx:CParser.LogicalOrExpressionContext):
        if ctx.logicalOrExpression():
            return self.visit(ctx.logicalOrExpression()) + ' || ' + self.visit(ctx.equalityExpression())
        else:
            return self.visit(ctx.equalityExpression())

    def visitEqualityExpression(self, ctx:CParser.EqualityExpressionContext):
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

    def visitRelationalExpression(self, ctx:CParser.RelationalExpressionContext):
        if len(ctx.children) > 1:
            return self.visit(ctx.castExpression(0)) + ' ' + ctx.children[1].getText() + ' ' + self.visit(ctx.castExpression(1))
        else:
            return self.visit(ctx.castExpression(0))

    def visitCastExpression(self, ctx:CParser.CastExpressionContext):
        if ctx.unaryExpression():
            return self.visit(ctx.unaryExpression())
        else:
            return ' '.join([self.visit(x) for x in ctx.children])

    def visitUnaryExpression(self, ctx:CParser.UnaryExpressionContext):
        if len(ctx.children) > 1:
            return ctx.children[0].getText() + ' ' + self.visit(ctx.postfixExpression())
        else:
            return self.visit(ctx.postfixExpression())

    def visitPostfixExpression(self, ctx:CParser.PostfixExpressionContext):
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

    def visitPrimaryExpression(self, ctx:CParser.PrimaryExpressionContext):
        return ctx.children[0].getText()

    def visitExpression(self, ctx:CParser.ExpressionContext):
        return ', '.join([self.visit(x) for x in ctx.assignmentExpression()])

    def visitCompoundStatement(self, ctx):
        return '\n{\n' + addIndentation('\n'.join([self.visit(i) for i in ctx.children[1:-1]])) + '\n}'

    def visitBlockItem(self, ctx):
        if ctx.statement():
            return self.visit(ctx.statement())
        return self.visit(ctx.declaration())

    def visitInitDeclaratorList(self, ctx):
        print("text",ctx.getText())
        return self.visit(ctx.initDeclarator())

    def visitInitDeclarator(self, ctx):
        if ctx.initializer():
            # 如果有赋值语句，就返回值和变量名；否则只返回变量名
            return ctx.declarator().getText(), ctx.initializer().getText()
        return ctx.declarator().getText()

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
            if_statements = f'if({self.visit(ctx.expression())})' + self.visit(ctx.statement(0))
            else_statement = ''
            if len(ctx.children) > 5:
                else_statement = '\nelse' + self.visit(ctx.statement(1))
            return if_statements + else_statement
        if txt == 'while':
            return f'while({self.visit(ctx.expression())})' + self.visit(ctx.statement(0))
        if txt == 'for':
            forDeclaration = ctx.forDeclaration()
            forDeclaration = '' if not forDeclaration else self.visit(forDeclaration)
            forExpression_0 = ctx.forExpression(0)
            forExpression_0 = '' if not forExpression_0 else self.visit(forExpression_0)
            forExpression_1 = ctx.forExpression(1)
            forExpression_1 = '' if not forExpression_1 else self.visit(forExpression_1)
            return f'for ({forDeclaration}; {forExpression_0}; {forExpression_1})' + self.visit(ctx.statement(0))
        if txt == 'return':
            expression = ''
            if ctx.expression():
                expression = self.visit(ctx.expression())
            return f'return {expression};'
        return ctx.getText()

    def visitForDeclaration(self, ctx:CParser.ForDeclarationContext):
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
        if len(ctx.children) == 1:
            return self.visit(ctx.parameterList()), False
        else:
            return self.visit(ctx.parameterList()), True

    def visitParameterList(self, ctx: CParser.ParameterListContext):
        """
            parameterList
                :   parameterDeclaration
                |   parameterList ',' parameterDeclaration
                ;
            :param ctx:
            :return: 返回变量名字列表arg_names和变量类型列表arg_types
        """
        if len(ctx.children) == 1:
            arg_list = []
        else:
            arg_list = self.visit(ctx.parameterList())
        item = self.visit(ctx.parameterDeclaration())
        arg_list.append(item)
        return arg_list

    def visitParameterDeclaration(self, ctx: CParser.ParameterDeclarationContext):
        return self.visit(ctx.typeSpecifier()) + ' ' + self.visit(ctx.declarator())

    def visitParameterDeclaration2(self, ctx: CParser.ParameterDeclarationContext):
        return self.visit(ctx.declarator())

def main(argv):
    input = FileStream('test.c' if len(argv) <= 1 else argv[1])
    lexer = CLexer(input)
    stream = CommonTokenStream(lexer)
    parser = CParser(stream)
    tree = parser.compilationUnit()
    _visitor = ToJSVisitor()
    ans=_visitor.visit(tree)
    outfile = open('test.ll' if len(argv) <= 2 else argv[2], 'w', encoding='utf-8')
    outfile.write(repr(_visitor.module))
    outfile.close()
    print(repr(_visitor.module))

if __name__ == '__main__':
    main(['main', 'test.c'])