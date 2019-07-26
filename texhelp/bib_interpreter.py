# -*- coding: utf-8 -*-

import geninterp
import re
import os

#____________________________________________________________________
# TeX blocks and interpreters


class StringBlock(geninterp.blocks.OpenCloseTagBlock):
    name = 'string'
    open_tag = '"'
    close_tag = '"'
    escape_char = '\\'
    forbid_new_openings = True

    @classmethod
    def open(cls, text, i):
        if not(cls.escape_char is None):
            if text[i-1] == cls.escape_char: return False
        return text[i:i+len(cls.open_tag)].lower() == cls.open_tag.lower()


class EntryBlock(geninterp.blocks.OpenCloseTagBlock):
    name = 'entry'
    close_tag = '}'
    escape_char = '\\'

    def __init__(self, i_begin, text):
        super(EntryBlock, self).__init__(i_begin, text)
        match = re.match(r'@\w+\{', text[i_begin:i_begin+50])
        self.open_tag = match.group()
        self.entry_type = self.open_tag[1:-1].lower()

    @classmethod
    def open(cls, text, i):
        if not(cls.escape_char is None):
            if text[i-1] == cls.escape_char: return False
        if text[i] == '@':
            return True


class BibInterpreter(geninterp.Interpreter):
    """docstring for BaseTexInterpreter"""
    blocks = [
        StringBlock,
        EntryBlock,
        ]

