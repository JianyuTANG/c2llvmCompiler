class StructTable:
    def __init__(self):
        self.type_list = {}

    def getValue(self, name):
        if name not in self.type_list.keys():
            return None
        return self.type_list[name]

    def insert(self, name, value):
        self.type_list[name] = value


class FuncTable:
    def __init__(self):
        self.func_list = {}

    def getValue(self, name):
        if name not in self.func_list.keys():
            return None
        return self.func_list[name]

    def insert(self, name, value):
        self.func_list[name] = value
