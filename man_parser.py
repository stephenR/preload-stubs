#!/usr/bin/env python

from config import MAN_PATH
import gzip
import re
import string
from function_declaration import Arg, FunctionDeclaration

class ManParser(object):
    def __init__(self, name):
        self.name = name
        self.synopsis = []
        in_synopsis = False
        for line in gzip.open(MAN_PATH + '/man3/' + name + '.3.gz', 'r'):
            if line.startswith('.SH'):
                if in_synopsis:
                    break
                if 'SYNOPSIS' in line:
                    in_synopsis = True
                continue
            if not in_synopsis:
                continue
            without_formatting = self._remove_formatting(line[:-1])
            if without_formatting:
                self.synopsis.append(without_formatting)
    def _remove_formatting(self, line):
        if not line.startswith('.'):
            return line
        if not ' ' in line:
            return None
        line = line[line.find(' ')+1:]
        ret = ''
        escape = False
        for c in line:
            if escape:
                escape = False
                ret += c
                continue
            if c == '\\':
                escape = True
                continue
            if c == '"':
                continue
            ret += c
        return ret
    def header_files(self):
        includes = set([])
        for line in self.synopsis:
            match = re.search('#include <(.+)>', line)
            if not match:
                continue
            include = match.group(1)
            if include in includes:
                continue
            includes.add(include)
            yield include
    def declaration(self):
        for line in self.synopsis:
            match = re.search('^(.*[^\w]){} *\\((.*)\\);'.format(self.name), line)
            if not match:
                continue
            ret_type = match.group(1)
            args = map(string.strip, match.group(2).split(','))
            args = map(Arg, args)
            return FunctionDeclaration(self.header_files(), self.name, ret_type, args)

if __name__ == '__main__':
    import sys
    mp = ManParser(sys.argv[1])
    for header_file in mp.header_files():
        print header_file
    print mp.declaration()
