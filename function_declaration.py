#!/usr/bin/env python

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
    def __eq__(self, other):
        return self.type == other.type
    def __ne__(self, other):
        return not (self == other)

class FunctionDeclaration(object):
    def __init__(self, header_files, name, ret_type, arg_types, variadic):
        self.header_files = header_files
        self.name = name
        self.ret_type = ret_type
        self.arg_types = arg_types
        self.variadic = variadic

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

    def __eq__(self, other):
        if self.name != other.name:
            return False
        if self.ret_type != other.ret_type:
            return False
        if len(self.arg_types) != len(other.arg_types):
            return False
        if any(a != b for a,b in zip(self.arg_types, other.arg_types)):
            return False
        return True

    def __ne__(self, other):
        return not (self == other)
