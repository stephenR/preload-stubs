#!/usr/bin/env python

import os
import pickle
from man_parser import ManParser
from declaration_parser import DeclarationParserFactory

HEADER_BLACKlIST = ['dlg_keys.h', 'dlg_colors.h', 'dlg_config.h', 'dialog.h']

class DeclarationMap(object):
    def __init__(self):
        self.declarations = {}

    def add_file(self, rel_path, base_path):
        parser = DeclarationParserFactory.file_parser(rel_path, base_path)
        for declaration in parser.declarations():
            if declaration.name in self.declarations:
                continue
            try:
                declaration = ManParser(declaration.name).declaration()
            except:
                pass
            self.declarations[declaration.name] = declaration

    def add_directory(self, dirname):
        for root, dirs, files in os.walk(dirname):
            for header in files:
                if len(header) < 3 or header[-2:] != '.h':
                    continue
                if header in HEADER_BLACKlIST:
                    continue
                rel_path = root[len(dirname)+1:]
                self.add_file(os.path.join(rel_path, header), dirname)

def get_declarations(dir, files):
    declaration_map = DeclarationMap()
    if dir:
        declaration_map.add_directory(dir)
    if files:
        for header in files:
            declaration_map.add_file(header)
    return declaration_map.declarations

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Parse C header files for function prototypes.\n')
    parser.add_argument('-d', '--dir', help='include directory to parse, defaults to /usr/include if no individual files are given')
    parser.add_argument('-o', '--outfile', help='file to write the pickled declaration map to', default='declarations.p')
    parser.add_argument('header_files', nargs='*', help='header file to parse')
    args = parser.parse_args()

    if not (args.header_files or args.dir):
        args.dir = '/usr/include'

    declarations = get_declarations(args.dir, args.header_files)

    pickle.dump(declarations, open(args.outfile, 'w'))
