from unittest import TestCase

import texhelp
import logging


class TestTexInterpreter(TestCase):

    def setUp(self):
        self.interpreter = texhelp.TexInterpreter()

    def test_nothing(self):
        tree = self.interpreter.interpret('')
        self.assertEqual(tree.parse(), '')

    def test_onlyplain(self):
        tree = self.interpreter.interpret('aaaa')
        self.assertEqual(tree.parse(), 'aaaa')

    def test_comment(self):
        tree = self.interpreter.interpret('aaaa%bbbb')
        self.assertEqual(tree.parse(), 'aaaa')
        tree = self.interpreter.interpret('aaaa%bbbb\ncccc')
        self.assertEqual(tree.parse(), 'aaaacccc')

    def test_escaped_comment(self):
        tree = self.interpreter.interpret('aaaa\\%bbbb')
        self.assertEqual(tree.parse(), 'aaaa\\%bbbb')

    def test_cite(self):
        tree = self.interpreter.interpret('aaaa\cite{bbbb}')
        self.assertEqual(tree.parse(), 'aaaa\cite{bbbb}')
        tree = self.interpreter.interpret('aaaa\cite{bb%cc\nbb}')
        self.assertEqual(tree.parse(), 'aaaa\cite{bbbb}')


class TestBibInterpreter(TestCase):

    def setUp(self):
        self.interpreter = texhelp.BibInterpreter()

    def test_nothing(self):
        tree = self.interpreter.interpret('')
        self.assertEqual(tree.parse(), '')

    def test_basic(self):
        text = 'aaa@Article{field="bla"}bbb'
        tree = self.interpreter.interpret(text)
        entries = list(tree.gen_blocks_by_name('entry'))
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry.block.entry_type, 'article')
        self.assertEqual(entry.block.get_text_no_tags(), 'field="bla"')


class TestBibFormatter(TestCase):
    
    def setUp(self):
        self.formatter = texhelp.BibFormatter()

    def test_basic(self):
        text = (
            '@article{Higgs,\n'
            '    author = "Higgs, Peter W.",\n'
            '    title  = "Broken {S}ymmetries, and the {M}asses of {G}auge {B}osons"\n'
            '    }'
            )
        citation = self.formatter.get_citation(text)
        logging.debug('Given:\n{0}'.format(text))
        logging.debug('Processed:\n{0}'.format(citation.parse()))
        self.assertEqual(citation.parse(), text)

    def test_bigref(self):
        text = """@article{Aad:2014tca,
    author        = "Aad, Georges and others",
    title         = "Fiducial and differential cross sections of {H}iggs boson production measured in the four-lepton decay channel in {$pp$} collisions at {$\sqrt{s}$} = 8 {TeV} with the {ATLAS} detector",
    collaboration = "ATLAS",
    journal       = "Phys. Lett. B",
    volume        = "738",
    year          = "2014",
    pages         = "234",
    doi           = "10.1016/j.physletb.2014.09.054",
    eprint        = "1408.3226",
    archivePrefix = "arXiv",
    primaryClass  = "hep-ex",
    reportNumber  = "CERN-PH-EP-2014-186",
    SLACcitation  = "%%CITATION = ARXIV:1408.3226;%%"
    }"""
        citation = self.formatter.get_citation(text)
        logging.debug('Given:\n{0}'.format(text))
        logging.debug('Processed:\n{0}'.format(citation.parse()))
        self.assertEqual(citation.parse(), text)


class TestBibTitleFormatter(TestCase):

    def setUp(self):
        self.formatter = texhelp.bib_formatter.CMSCiteFormatter('bogus', 'bogus')

    def test_titles(self):
        self.assertEqual(
            self.formatter.get_reinterpreted_title('Two Words'), 'Two {W}ords'
            )
        self.assertEqual(
            self.formatter.get_reinterpreted_title('Two Words $u_{some_math}$'), 'Two {W}ords {$u_{some_math}$}'
            )
        self.assertEqual(
            self.formatter.get_reinterpreted_title('SU(3) $math$ GeV'), '{SU(3)} {$math$} {GeV}'
            )
        self.assertEqual(
            self.formatter.get_reinterpreted_title('at {$\sqrt{s}$} = 8 {TeV} with'), 'at {$\sqrt{s}$} = 8 {TeV} with'
            )
        




