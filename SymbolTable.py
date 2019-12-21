def createTable(currentTable=None):
    newTable = SymbolTable(currentTable)
    currentTable.addChild(newTable)
    return newTable


class SymbolTable:
    def __init__(self, father):
        self.symbol_list = {}
        self.children = []
        self.father = father

    def addChild(self, child):
        self.children.append(child)

    def getFather(self):
        return self.father

    def getDetail(self, name):
        if name not in self.symbol_list.keys():
            if self.father:
                return self.father.getDetail(name)
            else:
                return None
        return self.symbol_list[name]

    def insert(self, name, detail):
        self.symbol_list[name] = detail


class ArrayType:
    def __init__(self):
        self.length = 0
        self.child_type = None


class BasicType:
    def __init__(self):
        self.llvm_type = None
