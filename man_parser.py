#!/usr/bin/env python

from config import MAN_PATH
import gzip
import re
import string
from declaration_parser import DeclarationParserFactory

class ManParser(object):
    def __init__(self, name):
        self._header_files = None
        self.name = name
        self.synopsis = []
        in_synopsis = False
        continue_line = None
        try:
            fd = gzip.open(MAN_PATH + '/man3/' + name + '.3.gz', 'r')
        except:
            fd = gzip.open(MAN_PATH + '/man2/' + name + '.2.gz', 'r')
        for line in fd:
            if continue_line != None:
                line = continue_line + line
                continue_line = None
            if line[-2:] == '\\\n':
                continue_line = line[:-2]
                continue
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
        if self._header_files:
            return self._header_files

        includes = set([])
        self._header_files = []
        for line in self.synopsis:
            match = re.search('#include <(.+)>', line)
            if not match:
                continue
            include = match.group(1)
            if include in includes:
                continue
            includes.add(include)
            self._header_files.append(include)

        return self._header_files

    def declaration(self):
        for line in self.synopsis:
            match = re.search('^.*[^\w]{} *\\(.*\\);'.format(self.name), line)

            if not match:
                continue

            parser =  DeclarationParserFactory.string_parser(match.group(0), headers=self.header_files())
            for declaration in parser.declarations():
                if declaration.name == self.name:
                    return declaration
            assert(False)
        #we opened a man file with the correct name, we should find the declaration
        assert(False)

if __name__ == '__main__':
    import sys
    mp = ManParser(sys.argv[1])
    for header_file in mp.header_files():
        print header_file
    print mp.declaration()
