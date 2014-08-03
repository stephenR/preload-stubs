#!/usr/bin/env python

from config import LIBCLANG_PATH
from function_declaration import FunctionDeclaration, Arg
import tempfile
import os

SKIP = '_PRELOAD_PARSER_SKIP_'
NO_SKIP = '_PRELOAD_PARSER_NO_SKIP_'

try:
    from config import LIBCLANG_PATH
except:
    LIBCLANG_PATH = None
import clang.cindex as ci

library_file_set = False

class DeclarationParser(object):
    def __init__(self, filename, base_path = '.', headers=None):
        global library_file_set
        self._skip = False
        self.tmp_file = None
        if not library_file_set and LIBCLANG_PATH:
            ci.Config.set_library_file(LIBCLANG_PATH)
            library_file_set = True
        if headers != None:
            self.headers = headers
        else:
            self.headers = [filename]
        index = ci.Index.create()
        self.cursor = index.parse(os.path.join(base_path, filename), options=ci.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD).cursor

    def __del__(self):
        if self.tmp_file:
            from os import remove
            remove(self.tmp_file)

    def _declarations(self, node):
        if node.kind.name == 'MACRO_DEFINITION':
            if node.spelling == SKIP:
                self._skip = True
            if node.spelling == NO_SKIP:
                self._skip = False
        if not self._skip and node.kind.is_declaration() and node.kind.name == "FUNCTION_DECL":
            yield self._parse_declaration(node)
        else:
            #print dir(node.get_arguments())
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
        for i, arg in enumerate(node.get_arguments()):
            arg_name = arg.spelling
            if not arg_name or arg_name == '':
                arg_name = 'arg' + str(i)
            args.append(Arg(arg.type.spelling, arg_name))

        return FunctionDeclaration(self.headers, name, ret_type, args)

class DeclarationParserFactory(object):
    @staticmethod
    def string_parser(string, headers=[]):
        body = '#define {}\n'.format(SKIP)
        body += '\n'.join('#include <{}>'.format(header) for header in headers)
        body += '\n#define {}\n'.format(NO_SKIP)
        body += string + ';\n'
        fd, tempname = tempfile.mkstemp(suffix='.h')
        os.write(fd, body)
        os.close(fd)
        dp = DeclarationParser(tempname, headers=headers)
        dp.tmp_file = tempname
        return dp
    @staticmethod
    def file_parser(filename, directory):
        dp = DeclarationParser(filename, directory)
        return dp

if __name__ == '__main__':
    dp = DeclarationParserFactory.string_parser('int f(int argc, void (*)(int)')
    decl = next(dp.declarations())
    print decl.header_files
    print decl
