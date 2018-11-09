from unittest import TestCase

import texhelp

class TestGetImages(TestCase):

    tex_file = 'tests/testtext.tex'

    def test_get_images(self):
        helper = texhelp.Helper(self.tex_file)

        expected_result = [
            'img/subdirectory/img1.pdf',
            'img/subdirectory/img2.pdf',
            'img/subdirectory/img3.pdf',
            ]

        self.assertEquals(
            helper.get_images(),
            expected_result
            )

    def test_get_figures(self):
        helper = texhelp.Helper(self.tex_file)

        expected_results = [
            {
                'imgs' : ['img/subdirectory/img1.pdf', 'img/subdirectory/img2.pdf'],
                'caption' : 'A few non-existent images',
                'label' : 'fig:thefirstfigure'
                },
            {
                'imgs' : ['img/subdirectory/img3.pdf'],
                'caption' : 'A caption { with internal } brackets',
                'label' : 'fig:thesecondfigure'
                },
            ]

        self.assertEquals(
            helper.get_figures(),
            expected_results
            )


class TestGetCitations(TestCase):

    tex_file = 'tests/testtext.tex'

    def setUp(self):
        self.helper = texhelp.Helper(self.tex_file)

    def test_remove_commented_part_from_line_regular(self):
        self.helper = texhelp.Helper(self.tex_file)
        line = 'aaaa%bbbbb'
        processed_line = self.helper.remove_commented_part_from_line(line)
        self.assertEquals(processed_line, 'aaaa')

    def test_remove_commented_part_from_line_escaped(self):
        self.helper = texhelp.Helper(self.tex_file)
        line = 'aaaa\\%bbbbb'
        processed_line = self.helper.remove_commented_part_from_line(line)
        self.assertEquals(processed_line, line)

    def test_remove_commented_part_from_line_complicated(self):
        line = 'a\\%b%c\\%d'
        processed_line = self.helper.remove_commented_part_from_line(line)
        self.assertEquals(processed_line, 'a\\%b')

    def test_basic_cite(self):
        line = 'aaaa \\cite{blabla} bbbb'
        citations, citation_counts = self.helper.get_cites(line)
        self.assertEquals(citations[0], 'blabla')

    def test_cite_count(self):
        line = 'aaaa \\cite{blabla} bbbb \\cite{blabla} cccc \\cite{bla2}'
        citations, citation_counts = self.helper.get_cites(line)
        self.assertEquals(citations, ['blabla', 'bla2'])
        self.assertEquals(citation_counts['blabla'], 2)




