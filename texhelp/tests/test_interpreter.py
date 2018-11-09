from unittest import TestCase

import texhelp
import logging


class TestInterpreter(TestCase):

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
