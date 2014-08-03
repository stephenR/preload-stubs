#!/usr/bin/env python

from config import MAN_PATH
import gzip
import re
import string
from declaration_parser import DeclarationParserFactory

BLACKLIST = ['open', 'openat', 'strerror_r', 'getpgrp', 'setpgrp', 'reboot', 'bdflush']

class ManParserException(Exception):
    def __init__(self, msg):
        super(ManParserException, self).__init__(msg)

class ManParser(object):
    def __init__(self, name):
        self._header_files = None
        self.name = name
        self.synopsis = []
        in_synopsis = False
        continue_line = None
        fd = None
        for i in [3,2]:
            try:
                fd = gzip.open(MAN_PATH + '/man{}/'.format(i) + name + '.{}.gz'.format(i), 'r')
                break
            except:
                pass
        if not fd:
            raise ManParserException('No man page found for {}.'.format(name))
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
        declarations = []

        for line in self.synopsis:
            match = re.search('^.*[^\w]{} *\\(.*\\);'.format(self.name), line)

            if not match:
                continue

            parser =  DeclarationParserFactory.string_parser(match.group(0), headers=self.header_files())
            for declaration in parser.declarations():
                if declaration.name == self.name:
                    declarations.append(declaration)
                    break

        #we opened a man file with the correct name, we should find the declaration
        #assert(len(declarations) >= 1)
        #TODO turn this into an assertion
        if len(declarations) < 1:
            raise ManParserException("[BUG] Error parsing the man page.")
        #if len(declarations) > 1:
        #    print 'multiple declarations: {}'.format(self.name)

        return declarations[0]

if __name__ == '__main__':
    import sys
    mp = ManParser(sys.argv[1])
    for header_file in mp.header_files():
        print header_file
    print mp.declaration()
