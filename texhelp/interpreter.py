import texhelp
import logging
import os.path as osp

from .blocks import *

class Interpreter(object):
    """docstring for Interpreter"""

    def __init__(self):
        super(Interpreter, self).__init__()
        self.filename = False
        self.blocks = [ BracketBlock ]

    def interpret_file(self, filename, reset_input_base=True):
        self.filename = filename
        with open(filename) as fp:
            raw_text = fp.read()
        if reset_input_base:
            InputBlock.base_path = osp.dirname(osp.abspath(self.filename))
        self.interpret(raw_text)

    def initialize(self):
        self.block_stack = []
        self.text_stack = ['']
        self.i = 0
        self.processed_blocks = { Block.name : [] for Block in self.blocks }

    def interpret(self, raw_text):
        self.initialize()
        self.raw_text = raw_text

        while self.i < len(self.raw_text):
            self.get_text_until_next_tag()
        
    def get_text_until_next_tag(self):
        i_begin = self.i

        if self.i >= len(self.raw_text):
            raise LookupError("Reached end of text")

        is_open = True
        while is_open:

            if self.i >= len(self.raw_text):
                if len(self.block_stack) > 0 and isinstance(self.block_stack[-1], CommentBlock):
                    pass
                else:
                    self.text_stack[-1] += self.raw_text[i_begin:]
                    break

            # Check if the last block on the stack is closed
            if len(self.block_stack) > 0:
                active_block = self.block_stack[-1]
                if active_block.close(self.raw_text, self.i):
                    # Get the text from the latest textblock,
                    # process it (usually returns the same),
                    # and add it to the next-on-the-stack textblock
                    # so it will be included in the .process() of the
                    # next block

                    active_textblock = self.text_stack.pop() + self.raw_text[i_begin:self.i]
                    active_block.processed_text = active_block.process(active_textblock)
                    self.text_stack[-1] += active_block.processed_text

                    
                    # Record the block as being processed (for later retrieval)
                    self.processed_blocks[active_block.name].append(active_block)

                    # Pop the block
                    self.block_stack.pop()

                    self.i += active_block.advance_index_at_close()

                    if active_block.has_subinterpreter:
                        subinterpreter = active_block.run_subinterpreter()
                        if not(subinterpreter is False):
                            for key in self.processed_blocks:
                                self.processed_blocks[key].extend(subinterpreter.processed_blocks[key])

                    return

            # If active block prevents opening of new blocks, don't run this code
            if len(self.block_stack) == 0 or not(self.block_stack[-1].no_allow_other_openings):

                # Check if the a new tag begins at the current index
                for Block in self.blocks:
                    if Block.open(self.raw_text, self.i):
                        # Open up the new block and append it to the stack
                        self.block_stack.append(Block(self.i))

                        # Add the newly created text block to the last textblock on the stack
                        # This is not to be processed by this block
                        self.text_stack[-1] += self.raw_text[i_begin:self.i]

                        # Open up a new entry to the stack (to be processed by this block)
                        self.text_stack.append('')

                        # Make sure to EXclude any opening characters in the current text block
                        self.i += self.block_stack[-1].advance_index_at_open()
                        return

            self.i += 1


class TexInterpreter(Interpreter):
    """docstring for TexInterpreter"""
    def __init__(self):
        super(TexInterpreter, self).__init__()
        self.blocks = [
            BracketBlock,
            CommentBlock,
            FigureBlock,
            IncludeGraphicsBlock,
            CiteBlock,
            InputBlock,
            LabelBlock
            ]

class BibInterpreter(Interpreter):
    """docstring for BibInterpreter"""
    def __init__(self):
        super(BibInterpreter, self).__init__()
        self.blocks = [
            BracketBlock,
            ArticleBlock,
            TechReportBlock,
            InProceedingsBlock,
            InCollectionBlock,
            MiscBlock,
            UnpublishedBlock,
            ]

    def interpret_file(self, filename):
        super(BibInterpreter, self).interpret_file(filename)
        self.get_dict()

    def get_dict(self):
        self.ordered_cites = []
        self.cite_dict = {}
        _i_blocks = []
        for kw, blocks in self.processed_blocks.iteritems():
            if kw == 'bracket': continue
            for block in blocks:
                key = block.get_citename()
                self.cite_dict[key] = block
                self.ordered_cites.append(key)
                _i_blocks.append(block.i_block)
        _i_blocks, self.ordered_cites = (list(t) for t in zip(*sorted(zip(_i_blocks, self.ordered_cites))))



class BibTitleInterpreter(Interpreter):
    """docstring for BibTitleInterpreter"""
    def __init__(self):
        super(BibTitleInterpreter, self).__init__()
        self.blocks = [
            BracketBlock,
            BibMathBlock,
            BibTextBlock
            ]
        


