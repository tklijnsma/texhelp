# -*- coding: utf-8 -*-

import geninterp
import re
import os

#____________________________________________________________________
# TeX blocks and interpreters

class BracketBlock(geninterp.blocks.OpenCloseTagBlock):
    name = 'bracket'
    open_tag = '{'
    close_tag = '}'
    escape_char = '\\'

class CommentBlock(geninterp.blocks.CommentBlock):
    name = 'comment'
    open_tag = '%'
    escape_char = '\\'

class InputBlock(geninterp.blocks.InputBlock):
    name = 'input'
    open_tag = '\\input{'
    close_tag = '}'
    extension = '.tex'
    escape_char = '\\'


class ImportBlock(geninterp.blocks.InputBlock):
    name = 'import'
    open_tag = '\\import{'
    close_tag = '}'
    extension = '.tex'
    escape_char = '\\'
    close_immediately = True

    _latest_import_relpath = '.'

    def __init__(self, i_begin, text):
        super(ImportBlock, self).__init__(i_begin, text)

        # Assume no comments
        look_ahead_segment = self.text[i_begin+len(self.open_tag)-1:i_begin+1000]
        self.matches = re.findall(r'\{.*?\}', look_ahead_segment)[:2]
        if len(self.matches) != 2:
            raise ValueError(
                'Error parsing ImportBlock: {0} matches, look_ahead_segment is:\n{1}'
                .format(len(self.matches), look_ahead_segment)
                )
        self.relpath_file = os.path.join(
            self.matches[0].replace('{','').replace('}',''), self.matches[1].replace('{','').replace('}','')
            )

        if self.name == 'import':
            # For SubImports, also record what the latest Import was
            ImportBlock._latest_import_relpath = self.matches[0].replace('{','').replace('}','')


    def process(self, text=None):
        return self.open_tag[-1] + self.matches[0] + self.matches[1]

    def run_subinterpreter(self, stub=None):
        print 'Running run_subinterpreter, relpath_file is {0}'.format(self.relpath_file)
        return super(ImportBlock, self).run_subinterpreter(self.relpath_file)

    def advance_index_at_open(self):
        return len(self.open_tag)-1 + len(self.matches[0]) + len(self.matches[1]) -1


class SubImportBlock(ImportBlock):
    name = 'subimport'
    open_tag = '\\subimport{'
    close_tag = '}'
    extension = '.tex'
    escape_char = '\\'
    close_immediately = True

    def __init__(self, i_begin, text):
        super(SubImportBlock, self).__init__(i_begin, text)
        self.relpath_file = os.path.join(ImportBlock._latest_import_relpath, self.relpath_file)



class CiteBlock(geninterp.blocks.OpenCloseTagBlock):
    name = 'cite'
    open_tag = '\\cite{'
    close_tag = '}'
    escape_char = '\\'

class SectionBlock(geninterp.blocks.OpenCloseTagBlock):
    name = 'section'
    open_tag = '\\section{'
    close_tag = '}'
    escape_char = '\\'

class SubSectionBlock(geninterp.blocks.OpenCloseTagBlock):
    name = 'subsection'
    open_tag = '\\subsection{'
    close_tag = '}'
    escape_char = '\\'

class SubSubSectionBlock(geninterp.blocks.OpenCloseTagBlock):
    name = 'subsubsection'
    open_tag = '\\subsubsection{'
    close_tag = '}'
    escape_char = '\\'

class SubSubSubSectionBlock(geninterp.blocks.OpenCloseTagBlock):
    name = 'subsubsubsection'
    open_tag = '\\subsubsubsection{'
    close_tag = '}'
    escape_char = '\\'


class NewCommandBlock(geninterp.blocks.OpenCloseTagBlock):
    name = 'newcommand'
    open_tag = '\\newcommand{'
    close_tag = '}'
    escape_char = '\\'

class ProvideCommandBlock(geninterp.blocks.OpenCloseTagBlock):
    name = 'providecommand'
    open_tag = '\\providecommand{'
    close_tag = '}'
    escape_char = '\\'


class FigureBlock(geninterp.blocks.OpenCloseTagBlock):
    name = 'figure'
    open_tag = '\\begin{figure}'
    close_tag = '\\end{figure}'
    escape_char = '\\'

class IncludeGraphicsBlock(geninterp.blocks.OpenCloseTagBlock):
    name = 'includegraphics'
    open_tag = '\\includegraphics'
    close_tag = '}'
    escape_char = '\\'

    def advance_index_at_open(self):
        self.square_brackets = ''
        r = len(self.open_tag)
        if self.text[self.i_begin+len(self.open_tag)] == '[':
            text = self.text[self.i_begin+len(self.open_tag):]
            self.square_brackets = re.match(r'\[.*?\]', text).group()
            r += len(self.square_brackets) + 1
        return r

    def process(self, text=None):
        if text is None:
            r = self.get_text()
        else:
            r = text
        return self.open_tag + self.square_brackets + '{' + r + self.close_tag



class BaseTexInterpreter(geninterp.Interpreter):
    """docstring for BaseTexInterpreter"""
    blocks = [
        BracketBlock,
        CommentBlock,
        InputBlock,
        ImportBlock,
        SubImportBlock,
        ]

class TexInterpreter(BaseTexInterpreter):
    blocks = BaseTexInterpreter.blocks + [
        CiteBlock,
        # 
        SectionBlock,
        SubSectionBlock,
        SubSubSectionBlock,
        SubSubSubSectionBlock,
        NewCommandBlock,
        ProvideCommandBlock,
        FigureBlock,
        IncludeGraphicsBlock,
        ]


