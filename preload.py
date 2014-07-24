#!/usr/bin/env python

import clang.cindex as ci
import sys
import string
from relocations import get_relocations
import os

HEADER="""\
#define _GNU_SOURCE
#include <dlfcn.h>

"""

class Arg(object):
    def __init__(self, type, name):
        self.type = type
        self.name = name
    def get_name(self, off):
        if self.name == '':
            return 'arg_' + str(off)
        else:
            return self.name
    def declaration(self, off):
        name = self.get_name(off)
        return self.type + ' ' + name

class FuncProto(object):
    def __init__(self, name, ret_type, arg_types):
        self.name = name
        self.ret_type = ret_type
        self.arg_types = arg_types

    def __str__(self):
        ret = self.ret_type + ' ' + self.name + '('
        ret += ', '.join(type.declaration(i) for i,type in enumerate(self.arg_types))
        ret += ')'
        return ret

    def as_func_ptr(self, name):
        ret = self.ret_type + ' (*' + name + ')('
        ret += ', '.join(type.declaration(i) for i,type in enumerate(self.arg_types))
        ret += ')'
        return ret
    def get_arg_names(self):
        ret = []
        for i, arg in enumerate(self.arg_types):
            ret.append(arg.get_name(i))
        return ret

def iterate_func_protos(node):
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
        yield FuncProto(name, ret_type, args)
    for c in node.get_children():
        for func_proto in iterate_func_protos(c):
            yield func_proto

def get_stub(func_proto):
    body = ''
    fp_name = 'orig_' + func_proto.name
    body += func_proto.as_func_ptr(fp_name) + ';\n'
    body += fp_name + ' = dlsym(RTLD_NEXT, "' + func_proto.name + '");\n'
    body += 'return (*' + fp_name + ')(' + ', '.join(func_proto.get_arg_names()) + ');'

    #indent the body
    body = '\n'.join(map(lambda l: '  ' + l, body.split('\n')))

    ret = str(func_proto) + '{\n'
    ret += body
    ret += '\n}'

    #comment out everything
    ret = '\n'.join(map(lambda l: '//' + l, ret.split('\n')))
    ret += '\n\n'

    return ret

def write_c_file(func_protos):
    libpreload_fd = open('libpreload.c', 'w')

    libpreload_fd.write(HEADER)
    for func_proto in func_protos:
        libpreload_fd.write(get_stub(func_proto))

    libpreload_fd.close()

if __name__ == '__main__':
    bin_name = sys.argv[1]

    ci.Config.set_library_file("/usr/lib/llvm-3.4/lib/libclang.so")


    rels = get_relocations(bin_name)
    assert(type(rels) == type(set()))

    func_protos = []

    for root, dirs, files in os.walk('/usr/include'):
        if rels == set():
            break
        for header in files:
            if header[-2:] != '.h':
                continue
            index = ci.Index.create()
            header = os.path.join(root, header)
            tu = index.parse(header)

            for func_proto in iterate_func_protos(tu.cursor):
                if func_proto.name in rels:
                    func_protos.append(func_proto)
                    rels.remove(func_proto.name)
    
    write_c_file(func_protos)

