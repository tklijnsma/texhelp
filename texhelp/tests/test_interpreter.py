from unittest import TestCase

import texhelp
import logging


class TestInterpreter(TestCase):

    def setUp(self):
        self.interpreter = texhelp.TexInterpreter()
        self.interpreter.initialize()

    def test_comment(self):
        self.interpreter.raw_text = 'aaaa%bbbb\ncccc%dddd'

        self.interpreter.get_text_until_next_tag()
        logging.debug('block_stack now: {0}'.format(self.interpreter.block_stack))
        logging.debug('text_stack now: {0}'.format(self.interpreter.text_stack))
        self.assertEqual(self.interpreter.text_stack[0], 'aaaa')
        self.assertEqual(self.interpreter.raw_text[self.interpreter.i], 'b')

        self.interpreter.get_text_until_next_tag()
        logging.debug('block_stack now: {0}'.format(self.interpreter.block_stack))
        logging.debug('text_stack now: {0}'.format(self.interpreter.text_stack))
        self.assertEqual(self.interpreter.text_stack[0], 'aaaa')

        self.interpreter.get_text_until_next_tag()
        logging.debug('block_stack now: {0}'.format(self.interpreter.block_stack))
        logging.debug('text_stack now: {0}'.format(self.interpreter.text_stack))
        self.assertEqual(self.interpreter.text_stack[0], 'aaaacccc')
        self.assertEqual(self.interpreter.text_stack[1], '')

        self.interpreter.get_text_until_next_tag()
        logging.debug('block_stack now: {0}'.format(self.interpreter.block_stack))
        logging.debug('text_stack now: {0}'.format(self.interpreter.text_stack))
        self.assertEqual(self.interpreter.text_stack[0], 'aaaacccc')


    def test_comment_with_other_comments_after_it(self):
        self.interpreter.raw_text = 'aaaa%bbbb%cccc'

        logging.debug('block_stack now: {0}'.format(self.interpreter.block_stack))
        logging.debug('text_stack now: {0}'.format(self.interpreter.text_stack))

        self.interpreter.get_text_until_next_tag()
        logging.debug('block_stack now: {0}'.format(self.interpreter.block_stack))
        logging.debug('text_stack now: {0}'.format(self.interpreter.text_stack))
        self.assertEqual(self.interpreter.text_stack[0], 'aaaa')

        self.interpreter.get_text_until_next_tag()
        logging.debug('block_stack now: {0}'.format(self.interpreter.block_stack))
        logging.debug('text_stack now: {0}'.format(self.interpreter.text_stack))
        self.assertEqual(self.interpreter.text_stack[0], 'aaaa')


    def test_basic_bracket(self):
        self.interpreter.raw_text = 'aaaa{bbbb}cccc'

        self.interpreter.get_text_until_next_tag()
        self.assertEqual(self.interpreter.text_stack[0], 'aaaa')

        self.interpreter.get_text_until_next_tag()
        self.assertEqual(self.interpreter.text_stack[0], 'aaaa{bbbb}')

        self.interpreter.get_text_until_next_tag()
        self.assertEqual(self.interpreter.text_stack[0], 'aaaa{bbbb}cccc')


    def test_nested_brackets(self):
        self.interpreter.raw_text = 'aa{bb{cccc}dd}ee'

        self.interpreter.get_text_until_next_tag()
        logging.debug('block_stack now: {0}'.format(self.interpreter.block_stack))
        logging.debug('text_stack now: {0}'.format(self.interpreter.text_stack))
        self.assertEqual(self.interpreter.text_stack[0], 'aa')


        self.interpreter.get_text_until_next_tag()
        logging.debug('block_stack now: {0}'.format(self.interpreter.block_stack))
        logging.debug('text_stack now: {0}'.format(self.interpreter.text_stack))
        self.assertEqual(self.interpreter.text_stack[0], 'aa')
        self.assertEqual(self.interpreter.text_stack[1], 'bb')

        self.interpreter.get_text_until_next_tag()
        logging.debug('block_stack now: {0}'.format(self.interpreter.block_stack))
        logging.debug('text_stack now: {0}'.format(self.interpreter.text_stack))
        self.assertEqual(self.interpreter.text_stack[0], 'aa')
        self.assertEqual(self.interpreter.text_stack[1], 'bb{cccc}')

        self.interpreter.get_text_until_next_tag()
        logging.debug('block_stack now: {0}'.format(self.interpreter.block_stack))
        logging.debug('text_stack now: {0}'.format(self.interpreter.text_stack))
        self.assertEqual(self.interpreter.text_stack[0], 'aa{bb{cccc}dd}')

        self.interpreter.get_text_until_next_tag()
        logging.debug('block_stack now: {0}'.format(self.interpreter.block_stack))
        logging.debug('text_stack now: {0}'.format(self.interpreter.text_stack))
        self.assertEqual(self.interpreter.text_stack[0], 'aa{bb{cccc}dd}ee')

    def test_comments_in_cite_block(self):
        text = (
            '~\cite{%\n'
            'Aad:2014lwa,Khachatryan:2015rxa,% ATLAS and CMS hgg, Run I\n'
            'Aad:2014tca,Khachatryan:2015yvw,% ATLAS and CMS hzz, Run I\n'
            'Aad:2016lvc,Khachatryan:2016vnn,% ATLAS and CMS hww, Run I\n'
            'Aaboud:2018xdt,Sirunyan:2018kta,% ATLAS and CMS hgg, Run II\n'
            'Aaboud:2017oem,CMS_AN_2016-442,% ATLAS and CMS hzz, Run II\n'
            'Aaboud:2018ezd% ATLAS combination Run II\n'
            '}.'
            )
        logging.debug('Interpretering the following text:\n{0}'.format(text))

        self.interpreter.interpret(text)

        logging.debug('Found the following blocks:')
        logging.debug(self.interpreter.processed_blocks)

        self.assertEqual(len(self.interpreter.processed_blocks['cite']), 1)
        self.assertEqual(
            self.interpreter.processed_blocks['cite'][0].processed_text,
            '\\cite{Aad:2014lwa,Khachatryan:2015rxa,Aad:2014tca,Khachatryan:2015yvw,Aad:2016lvc,Khachatryan:2016vnn,Aaboud:2018xdt,Sirunyan:2018kta,Aaboud:2017oem,CMS_AN_2016-442,Aaboud:2018ezd}'
            )




class TestInterpreterCounts(TestCase):

    def setUp(self):
        self.interpreter = texhelp.TexInterpreter()
        self.interpreter.initialize()

        self.text = """

{}

\\begin{figure}
    \\includegraphics{somepath.png}
\\end{figure}

% some comment

\cite{source}

a
"""

    def test_processed_blocks(self):
        self.interpreter.interpret(self.text)
        logging.debug('processed_blocks so far: {0}'.format(self.interpreter.processed_blocks))
        self.assertEqual(len(self.interpreter.processed_blocks['comment']), 1)
        self.assertEqual(len(self.interpreter.processed_blocks['cite']), 1)
        self.assertEqual(self.interpreter.processed_blocks['cite'][0].included_text, 'source')


class TestInterpreterInput(TestCase):

    def setUp(self):
        self.interpreter = texhelp.TexInterpreter()
        self.interpreter.initialize()

    def test_input_blocks_in_files(self):
        self.interpreter.interpret_file('tests/callsinput.tex')
        self.assertEqual(
            self.interpreter.processed_blocks['cite'][0].included_text,
            'test'
            )



class TestBibInterpreter(TestCase):
    """docstring for TestBibInterpreter"""

    def setUp(self):
        self.interpreter = texhelp.BibInterpreter()
        self.interpreter.initialize()

    def test_basic_bib(self):
        text = (
            '@article{deFlorian:2016spz,'
            + '\n' + 'author         = "de Florian, D. and others",'
            + '\n' + 'title          = "{Handbook of LHC Higgs Cross Sections: 4. Deciphering the Nature of the Higgs Sector}",'
            + '\n' + 'collaboration  = "LHC Higgs Cross Section Working Group",'
            + '\n' + 'doi            = "10.23731/CYRM-2017-002",'
            + '\n' + 'year           = "2016",'
            + '\n' + 'eprint         = "1610.07922",'
            + '\n' + 'archivePrefix  = "arXiv",'
            + '\n' + 'primaryClass   = "hep-ph",'
            + '\n' + 'reportNumber   = "FERMILAB-FN-1025-T, CERN-2017-002-M",'
            + '\n' + 'SLACcitation   = "%%CITATION = ARXIV:1610.07922;%%"'
            + '\n' + '}'
            )
        self.interpreter.interpret(text)

        self.assertEqual(
            len(self.interpreter.processed_blocks['article']), 1
            )
        self.assertEqual(
            self.interpreter.processed_blocks['article'][0].get_citename(), 'deFlorian:2016spz'
            )










