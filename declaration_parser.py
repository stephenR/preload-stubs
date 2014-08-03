#!/usr/bin/env python

from config import LIBCLANG_PATH
from function_declaration import FunctionDeclaration, Arg
import tempfile
import os

try:
    from config import LIBCLANG_PATH
except:
    LIBCLANG_PATH = None
import clang.cindex as ci

class DeclarationParser(object):
    def __init__(self, filename, headers=None):
        if LIBCLANG_PATH:
          ci.Config.set_library_file(LIBCLANG_PATH)
        if headers:
            self.headers = headers
        else:
            self.headers = [filename]
        index = ci.Index.create()
        self.cursor = index.parse(filename).cursor

    def __del__(self):
        if self.tmp_file:
            from os import remove
            remove(self.tmp_file)

    def _declarations(self, node):
        if node.kind.is_declaration() and node.kind.name == "FUNCTION_DECL":
            yield self._parse_declaration(node)
        else:
            for c in node.get_children():
                for declaration in self._declarations(c):
                    yield declaration

    def declarations(self):
        for declaration in self._declarations(self.cursor):
            yield declaration

    def _parse_declaration(self, node):
        name = node.spelling
        ret_type = node.type.get_result().spelling

        args = []
        for i, arg in enumerate(node.get_children()):
            if arg.type.kind == ci.TypeKind.INVALID:
                continue

            if arg.type.kind == ci.TypeKind.TYPEDEF:
                if arg.type.spelling == arg.spelling:
                    continue

            arg_name = arg.spelling
            if not arg_name or arg_name == '':
                arg_name = 'arg' + str(i)
            args.append(Arg(arg.type.spelling, arg_name))

        return FunctionDeclaration(self.headers, name, ret_type, args)

class DeclarationParserFactory(object):
    @staticmethod
    def string_parser(string, headers=[]):
        decl_str = string + ';\n'
        fd, tempname = tempfile.mkstemp(suffix='.h')
        os.write(fd, decl_str)
        os.close(fd)
        dp = DeclarationParser(tempname, headers)
        dp.tmp_file = tempname
        #decl_cursor = next(self._declarations())
        #ret_val = self._parse_cursor(decl_cursor)
        return dp
    @staticmethod
    def file_parser(filename):
        dp = DeclarationParser(filename)
        return dp

if __name__ == '__main__':
    dp = DeclarationParserFactory.string_parser('int f(int argc, void (*)(int)')
    print next(dp.declarations())
