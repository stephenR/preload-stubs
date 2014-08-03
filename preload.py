#!/usr/bin/env python

from relocations import get_relocations
import os
import argparse
import pickle

HEADER="""\
#define _GNU_SOURCE
#include <dlfcn.h>

"""

def get_stub(func_proto, comment=False):
    ret = ''
    body = ''

    fp_name = 'orig_' + func_proto.name

    body += func_proto.as_func_ptr(fp_name) + ';\n'
    body += fp_name + ' = dlsym(RTLD_NEXT, "' + func_proto.name + '");\n'
    body += 'return (*' + fp_name + ')(' + ', '.join(func_proto.get_arg_names()) + ');'

    #indent the body
    body = '\n'.join(map(lambda l: '  ' + l, body.split('\n')))

    for header_file in func_proto.header_files:
        ret += '#include <' + header_file + '>\n'
    ret += str(func_proto) + '{\n'
    ret += body
    ret += '\n}'

    if comment:
        ret = '\n'.join(map(lambda l: '//' + l, ret.split('\n')))

    ret += '\n\n'

    return ret

def write_c_file(func_protos, comment):
    libpreload_fd = open('libpreload.c', 'w')

    libpreload_fd.write(HEADER)
    for func_proto in func_protos:
        libpreload_fd.write(get_stub(func_proto, comment))

    libpreload_fd.close()

if __name__ == '__main__':
    script_path = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(description='Create a stub for an LD_PRELOADable library.')
    parser.add_argument('-b', '--binary', help='binary to scan for symbols')
    parser.add_argument('-d', '--declarations', help='declarations file as created by parse.py', default=script_path + '/declarations.p')
    parser.add_argument('-c', '--comment', help='comment out the created function stubs', action='store_true')
    parser.add_argument('function_names', metavar='function_name', nargs='*', help='function to create a stub for')
    args = parser.parse_args()

    if not (args.function_names or args.binary):
        parser.error('Nothing to do, add either function names or a binary to scan')

    try:
        pickled_declarations = open(args.declarations, 'r')
    except:
        parser.error('Error opening the declarations file. Did you run parse.py?')

    declarations = pickle.load(pickled_declarations)

    function_names = args.function_names or []
    function_names = set(function_names)

    if args.binary:
        rels = get_relocations(args.binary)
        assert(type(rels) == type(set()))
        function_names = function_names.union(rels)

    func_protos = []

    for function_name in function_names:
        try:
            func_protos.append(declarations[function_name])
        except:
            print 'No declaration found for {}'.format(function_name)

    write_c_file(func_protos, args.comment)

