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
        ]


