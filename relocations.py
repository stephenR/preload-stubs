#!/usr/bin/env python

from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection

def get_relocations(filename):
    ret = set()
    elffile = ELFFile(open(filename, 'r'))
    for section in elffile.iter_sections():
        if not isinstance(section, RelocationSection):
            continue

        # The symbol table section pointed to in sh_link
        symtable = elffile.get_section(section['sh_link'])

        for rel in section.iter_relocations():
            symbol = symtable.get_symbol(rel['r_info_sym'])
            if symbol['st_info']['type'] != 'STT_FUNC':
                continue
            # Some symbols have zero 'st_name', so instead what's used is
            # the name of the section they point at
            if symbol['st_name'] == 0:
                symsec = elffile.get_section(symbol['st_shndx'])
                symbol_name = symsec.name
            else:
                symbol_name = symbol.name
            ret.add(symbol_name)
    return ret

