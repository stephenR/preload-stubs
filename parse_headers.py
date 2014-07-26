#!/usr/bin/env python

import clang.cindex as ci
import os
import argparse
import pickle
from function_declaration import FunctionDeclaration, Arg
try:
  from config import LIBCLANG_PATH
except:
  LIBCLANG_PATH = None

class HeaderParser(object):
    def __init__(self, filename, dir=None):
        self.filename = filename
        self.dir = dir

    def _function_declarations(self, node):
        if node.kind.is_declaration() and node.kind.name == "FUNCTION_DECL":
            name = node.spelling
            ret_type = node.type.get_result().spelling

            args = []
            for arg in node.get_children():
                if arg.type.kind == ci.TypeKind.INVALID:
                    continue

                if arg.type.kind == ci.TypeKind.TYPEDEF:
                    if arg.type.spelling == arg.spelling:
                        continue

                args.append(Arg(arg.type.spelling, arg.spelling))
            yield FunctionDeclaration(self.filename, name, ret_type, args)

        for c in node.get_children():
            for declaration in self._function_declarations(c):
                yield declaration

    def function_declarations(self):
        index = ci.Index.create()

        if self.dir:
          abs_path = os.path.join(self.dir, self.filename)
        else:
          abs_path = self.filename
        tu = index.parse(abs_path)

        for declaration in self._function_declarations(tu.cursor):
            yield declaration

class DeclarationMap(object):
    def __init__(self):
        self.declarations = {}

    def add_file(self, filename, dir=None):
        parser = HeaderParser(filename, dir)
        for declaration in parser.function_declarations():
            self.declarations[declaration.name] = self.declarations.get(declaration.name, []) + [declaration]

    def add_directory(self, dirname):
        for root, dirs, files in os.walk(dirname):
            for header in files:
                if len(header) < 3 or header[-2:] != '.h':
                    continue
                rel_path = root[len(dirname)+1:]
                self.add_file(os.path.join(rel_path, header), dirname)

def get_declarations(dir, files):
    if LIBCLANG_PATH:
      ci.Config.set_library_file(LIBCLANG_PATH)

    declaration_map = DeclarationMap()
    if dir:
        declaration_map.add_directory(dir)
    if files:
        for header in files:
            declaration_map.add_file(header)
    return declaration_map.declarations

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parse C header files for function prototypes.\n')
    parser.add_argument('-d', '--dir', help='include directory to parse, defaults to /usr/include if no individual files are given')
    parser.add_argument('-o', '--outfile', help='file to write the pickled declaration map to', default='declarations.p')
    parser.add_argument('header_files', nargs='*', help='header file to parse')
    args = parser.parse_args()

    if not (args.header_files or args.dir):
        args.dir = '/usr/include'

    declarations = get_declarations(args.dir, args.header_files)

    pickle.dump(declarations, open(args.outfile, 'w'))
