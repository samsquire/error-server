import ast
from pprint import pprint
import sys
from importlib import import_module 

seenfiles = {}

class Walker(ast.NodeVisitor):
    def __init__(self, look_for_exceptions=False, line=None, exceptions=set()):
        self.seen = {}
        self.calls = {}
        self.look_for_exceptions = look_for_exceptions
        self.exceptions = exceptions
        self.lineno = line
        self.names = {}

    def visit_Import(self, node): 
        self.generic_visit(node)
        for name in node.names:
            self.seen[name.name] = node
        # pprint(ast.dump(node))
        
    def visit_Call(self, node): 
        self.generic_visit(node)
        # pprint(ast.dump(node))
        run = False
        if str(node.lineno) == str(self.lineno) or self.lineno == None:
            run = True
        if run and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            self.calls[node.func.attr] = node.func.value.id

        if run and isinstance(node.func, ast.Name):
            if node.func.id in self.names:
                attr = self.names[node.func.id] 
                self.calls[attr] = node.func.id

    def visit_ImportFrom(self, node): 
        self.generic_visit(node)
        # pprint(ast.dump(node))
        self.seen[node.module] = node
        for func in node.names:
            # print(func.name)
            self.names[func.name] = node.module

    def visit_Raise(self, node):
        self.generic_visit(node)
        # pprint(ast.dump(node))
        if self.look_for_exceptions and isinstance(node.exc, ast.Call):
            if isinstance(node.exc.func, ast.Name):
                self.exceptions.add(node.exc.func.id)
        # pprint(ast.dump(node))

    def find_exceptions(self):
        # print(self.seen)
        remove = []
        for k, v in self.calls.items():
            if v not in self.seen: 
                remove.append(k)

        for k, v in self.calls.items():
            imported = None
            try:
                imported = import_module(k, package=v) 
            except Exception as e:
                try:
                    imported = import_module(v) 
                except Exception as n:
                    pass
            if hasattr(imported, "__file__") and seenfiles.get(imported.__file__, False) == False:
                seenfiles[imported.__file__] = True
            
                if "so" in imported.__file__:
                    continue
                # print(imported.__file__)
                tree = ast.parse(open(imported.__file__).read())  

                walker = Walker(True, exceptions=self.exceptions)
                walker.visit(tree)
                walker.find_exceptions()
            

filename = sys.argv[1]
lineno = sys.argv[2]

def find_exceptions(lineno, fileobject):
    tree = ast.parse(fileobject.read())
    exceptions = set()
    walker = Walker(line=lineno, exceptions=exceptions)
    walker.visit(tree)
    # pprint(ast.dump(tree))
    walker.find_exceptions()
    for exception in walker.exceptions:
        print(exception)

find_exceptions(lineno, open(filename))
