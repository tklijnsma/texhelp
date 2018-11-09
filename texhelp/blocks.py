import texhelp
import logging
import os.path as osp
import re
import sys

class BaseBlock(object):
    """docstring for BaseBlock"""
    name = 'base'
    has_subinterpreter = False
    n_blocks = 0

    def __init__(self, i_begin):
        super(BaseBlock, self).__init__()
        self.i_begin = i_begin
        self.raw_text = ''
        self.i_close_is_eof = False
        self.no_allow_other_openings = False

        self.i_block = BaseBlock.n_blocks
        BaseBlock.n_blocks += 1


    def process(self, text):
        return text


class OpenCloseTagBlock(BaseBlock):
    """docstring for OpenCloseTagBlock"""
    open_tag = ''
    close_tag = ''
    case_sensitive = True

    def __init__(self, i_begin):
        super(OpenCloseTagBlock, self).__init__(i_begin)

    @classmethod
    def open(cls, raw_text, i):
        if cls.case_sensitive:
            return raw_text[i:i+len(cls.open_tag)] == cls.open_tag
        else:
            return raw_text[i:i+len(cls.open_tag)].lower() == cls.open_tag.lower()
        
    def close(self, raw_text, i):
        if self.case_sensitive:
            r = raw_text[i:i+len(self.close_tag)] == self.close_tag
        else:
            r = raw_text[i:i+len(self.close_tag)].lower() == self.close_tag.lower()
        if r:
            self.included_text = raw_text[self.i_begin+len(self.open_tag):i]
        return r

    def advance_index_at_open(self):
        return len(self.open_tag)

    def advance_index_at_close(self):
        return len(self.close_tag)

    def process(self, text):
        return self.open_tag + text + self.close_tag

    def get_processed_text_without_brackets(self):
        if not hasattr(self, 'processed_text'):
            raise RuntimeError('Block {0} is not processed yet.'.format(self))
        text = self.processed_text
        if text.startswith(self.open_tag):
            text = text.replace(self.open_tag, '', 1)
        if text.endswith(self.close_tag):
            text = text[:len(text)-len(self.close_tag)]
        return text


class BracketBlock(OpenCloseTagBlock):
    name = 'bracket'
    open_tag = '{'
    close_tag = '}'


class FigureBlock(OpenCloseTagBlock):
    name = 'figure'
    open_tag = '\\begin{figure}'
    close_tag = '\\end{figure}'


class IncludeGraphicsBlock(OpenCloseTagBlock):
    name = 'image'
    open_tag = '\\includegraphics{'
    close_tag = '}'


class CiteBlock(OpenCloseTagBlock):
    name = 'cite'
    open_tag = '\\cite{'
    close_tag = '}'
    def get_cites(self):
        comma_separated_cites = self.processed_text.replace(self.open_tag, '').replace(self.close_tag, '')
        return [ c.strip() for c in comma_separated_cites.split(',') ]


class LabelBlock(OpenCloseTagBlock):
    name = 'label'
    open_tag = '\\label{'
    close_tag = '}'


class CommentBlock(BaseBlock):
    """docstring for CommentBlock"""
    name = 'comment'

    def __init__(self, i_begin):
        super(CommentBlock, self).__init__(i_begin)
        self.no_allow_other_openings = True
        self.yield_empty_text = True

    @staticmethod
    def open(raw_text, i):
        # Mind the weird scenario where the first char of doc is % and the last \...
        return (raw_text[i] == '%' and not(raw_text[i-1] == '\\'))

    def close(self, raw_text, i):
        if i == len(raw_text):
            # EOF
            self.i_end = i-1
            self.raw_text = raw_text[self.i_begin:self.i_end+1]
            logging.debug('Comment {0} is closed by EOF'.format(self))
            self.i_close_is_eof = True
            return True

        if raw_text[i] == '\n':
            self.i_end = i
            self.raw_text = raw_text[self.i_begin:self.i_end+1]
            return True

        return False

    def advance_index_at_open(self):
        return 1

    def advance_index_at_close(self):
        if self.i_close_is_eof: return 0
        return 1

    def process(self, text):
        if self.yield_empty_text: return ''
        r =  '%' + text
        if not(self.i_close_is_eof): r += '\n'
        return r


class InputBlock(OpenCloseTagBlock):
    """docstring for InputBlock"""
    name = 'input'
    open_tag = '\\input{'
    close_tag = '}'
    base_path = ''
    has_subinterpreter = True

    def __init__(self, i_begin):
        super(InputBlock, self).__init__(i_begin)

    def close(self, raw_text, i):
        r = super(InputBlock, self).close(raw_text, i)
        return r

    def run_subinterpreter(self):
        # Here file opening code
        input_tex_file = osp.join(self.base_path, self.included_text)
        subinterpreter = texhelp.TexInterpreter()
        if not osp.isfile(input_tex_file):
            logging.warning('No file \'{0}\'; not running this input'.format(input_tex_file))
            return False
        subinterpreter.interpret_file(input_tex_file, reset_input_base=False)
        return subinterpreter


class BibBlock(OpenCloseTagBlock):
    close_tag = '}'
    case_sensitive = False

    pages_only_first = True

    def __init__(self, i_begin):
        super(BibBlock, self).__init__(i_begin)
        self.keys = []
        self.values = {}
        self._has_citename = False
        self._is_a_pas = None

    def get_citename(self):
        if not self._has_citename:
            self.citename = self.included_text.split(',',1)[0]
            self._has_citename = True
        return self.citename

    def get_reformatted_text(self):
        self.get_fields()
        text = []
        text.append(self.open_tag.lower() + self.get_citename() + ',')

        max_key_length = max(map(len, self.keys))
        for key in self.keys:
            field = '    {0:{keywidth}} = "{1}"'.format(
                key, self.values[key], keywidth=max_key_length
                )
            if key != self.keys[-1]:
                field += ','
            text.append(field)

        text.append('    ' + self.close_tag)
        return '\n'.join(text)

    def get_fields(self):
        rawtext = self.get_processed_text_without_brackets().split(',',1)[1] # Strip off the citename
        pat = r'(\w+)\s*?=\s*?\"([\w\W]*?)(?<!\\)\"\s*?,?'
        matches = re.findall(pat, rawtext)
        for match in matches:
            key = match[0].lower()
            for option in [ 'archivePrefix', 'primaryClass', 'reportNumber', 'SLACcitation' ]:
                if key == option.lower(): key = option        
            value = match[1]
            lines = []
            for line in value.split('\n'):
                line = line.strip()
                lines.append(line)
            value = ' '.join(lines)

            self.keys.append(key)
            self.values[key] = value
        self.process_keys()

    def process_keys(self):
        self.remove_key('issue')

        if not 'year' in self.keys:
            self.error('Found no key \'year\'.')

        if 'href' in self.keys:
            self.error(
                'Found key \'href\' (=\"{1}\"), which should probably be replaced by \'url\''
                .format(self.values['href'])
                )

        if 'pages' in self.keys and '-' in self.values['pages']:
            self.warning('Found a range of pages: \"{0}\"'.format(self.values['pages']))
            self.values['pages'] = self.values['pages'].split('-')[0].strip()

        if 'doi' in self.keys and 'url' in self.keys:
            self.warning('Found a url key even though a doi is specified')
            self.remove_key('url')

        if not 'doi' in self.keys:
            self.warning('No doi field found')

        if 'collaboration' in self.keys:
            if 'collaboration' in self.values['collaboration'].lower():
                self.warning(
                    'Found keyword \'collaboration\' in collaboration field,'
                    ' this should probably be removed: \"{0}\"'
                    .format(self.values['collaboration'])
                    )

        if self.is_a_pas():
            if not 'type' in self.keys:
                self.warning('Is a PAS, but no field \'type\' found.')
                self.keys.append('type')
                self.values['type'] = '{CMS Physics Analysis Summary}'
            if self.open_tag != '@techreport{':
                self.warning('Is a PAS, but not a @techreport.')
                self.open_tag = '@techreport{'
            if not 'number' in self.keys:
                if 'reportNumber' in self.keys:
                    self.warning(
                        'Found no key \'number\', but found \'reportNumber\'; using that instead'
                        )
                    self.keys.append('number')
                    self.values['number'] = self.values['reportNumber']
                    self.remove_key('reportNumber')
                else:
                    self.error(
                        'No key \'number\' or \'reportNumber\'; \'number\' should be specified!'
                        )

        if not 'title' in self.keys:
            self.error('Found no key \'title\'.')
        else:
            optimized_title = self.get_reinterpreted_title(self.values['title'])
            if not self.values['title'] == optimized_title:
                logging.warning(
                    'Replacing title:\n'
                    'Old: \"{0}\"\nNew: \"{1}\"'
                    .format(self.values['title'], optimized_title)
                    )
                if not 'ignoredoldtitle' in self.keys: self.keys.append('ignoredoldtitle')
                self.values['ignoredoldtitle'] = self.values['title']
                self.values['title'] = optimized_title

        if 'journal' in self.keys and 'volume' in self.keys:
            match = re.match(r'([a-zA-Z])', self.values['volume'][0])
            if match:
                vol_letter = match.group(1)
                new_journal_name = self.values['journal'].strip() + ' ' + vol_letter.upper()
                self.warning(
                    'Detected a volume starting with a letter: {0}; '
                    'changing journal from "{1}" to "{2}"'
                    .format(self.values['volume'], self.values['journal'], new_journal_name)
                    )
                self.values['journal'] = new_journal_name
                self.values['volume'] = self.values['volume'][1:]

        if 'number' in self.keys and not self.is_a_pas():
            logging.warning('Removing \'number\' key: {0}'.format(self.values['number']))
            self.remove_key('number')

        if 'type' in self.keys:
            if not(self.values['type'].startswith('{')):
                self.warning('Adding opening bracket to type field')
                self.values['type'] = '{' + self.values['type']
            if not(self.values['type'].endswith('}')):
                self.warning('Adding closing bracket to type field')
                self.values['type'] += '}'

        if 'collaboration' in self.keys:
            if 'atlas' in self.values['collaboration'].lower() and 'cms' in self.values['collaboration'].lower():
                self.warning(
                    'Detected ATLAS and CMS in the collaboration field; '
                    'Putting \'{ATLAS and CMS Collaborations}\' in the '
                    'author field instead.'
                    )
                if not 'author' in self.keys: self.keys.append('author')
                self.values['author'] = '{ATLAS and CMS Collaborations}'
                self.remove_key('collaboration')


    def remove_key(self, key):
        if key in self.keys:
            self.keys.remove(key)
            self.values.pop(key)

    def is_a_pas(self):
        if self._is_a_pas is None:
            self._is_a_pas = False
            for key in [ 'number', 'reportNumber' ]:
                if key in self.keys:
                    if 'cms-pas' in self.values[key].lower():
                        self._is_a_pas = True
                        break
            else:
                if 'type' in self.keys:
                    if 'CMS Physics Analysis Summary' in self.values['type']:
                        self._is_a_pas = True
        return self._is_a_pas

    def format_text_for_logging(self, text):
        return 'Ref {0}: {1}'.format(self.get_citename(), text)

    def debug(self, text):
        logging.debug(self.format_text_for_logging(text))

    def warning(self, text):
        logging.warning(self.format_text_for_logging(text))

    def error(self, text):
        logging.error(self.format_text_for_logging(text))




    def get_reinterpreted_title(self, title):
        blocks = self.get_ordered_title_blocks(title)
        new_title = self.process_sorted_title_blocks(blocks)
        return new_title

    def get_ordered_title_blocks(self, title):
        title = title.strip()
        
        # Interpret once to get the text with <begintext> and <endtext> brackets
        titleinterpreter = texhelp.BibTitleInterpreter()
        titleinterpreter.interpret(title)

        # Get pieces of text and math blocks
        bracketed_text = '<begintext>' + titleinterpreter.text_stack[0] + '<endtext>'
        self.debug('Bracketed text: "{0}"'.format(bracketed_text))

        titleinterpreter2 = texhelp.BibTitleInterpreter()
        titleinterpreter2.blocks.remove(BracketBlock)
        titleinterpreter2.interpret(bracketed_text)

        blocks = titleinterpreter2.processed_blocks['bibtextblock'] + titleinterpreter2.processed_blocks['bibmathblock']
        blocks.sort(key = lambda b: b.i_block)
        return blocks

    def process_sorted_title_blocks(self, blocks):
        new_title = ''
        for block in blocks:
            if isinstance(block, BibMathBlock):
                # Math blocks have their raw text passed
                new_title += '{$' + block.included_text + '$}'
            else:
                # Text blocks are processed
                new_title += block.get_bracketed_capitals()

        self.debug('New title:')
        self.debug(new_title)
        return new_title




class ArticleBlock(BibBlock):
    name = 'article'
    open_tag = '@article{'

class TechReportBlock(BibBlock):
    name = 'techreport'
    open_tag = '@techreport{'

class InProceedingsBlock(BibBlock):
    name = 'inproceedings'
    open_tag = '@inproceedings{'

class InCollectionBlock(BibBlock):
    name = 'incollection'
    open_tag = '@incollection{'

class MiscBlock(BibBlock):
    name = 'misc'
    open_tag = '@misc{'

class UnpublishedBlock(BibBlock):
    name = 'unpublished'
    open_tag = '@unpublished{'



class BibMathBlock(OpenCloseTagBlock):
    name = 'bibmathblock'
    open_tag = '$'
    close_tag = '$'

    def __init__(self, i_begin):
        super(OpenCloseTagBlock, self).__init__(i_begin)
        self.no_allow_other_openings = True

    def process(self, text):
        return '<endtext>$' + text + '$<begintext>'


class BibTextBlock(OpenCloseTagBlock):
    name = 'bibtextblock'
    open_tag = '<begintext>'
    close_tag = '<endtext>'

    def __init__(self, i_begin):
        super(OpenCloseTagBlock, self).__init__(i_begin)
        self.no_allow_other_openings = True

    def process(self, text):
        return text

    def get_bracketed_capitals(self):
        bracketed_capitals_text = []
        words = self.included_text.split(' ')
        for word in words:
            word = word.replace('{','').replace('}','')
            if len(word) == 0:
                pass
            elif not(re.search(r'[a-zA-Z]+', word)):
                pass
            elif word == word.capitalize() and not word.isdigit():
                if word != words[0]:
                    word = '{' + word[0].upper() + '}' + word[1:]
            elif word.lower() != word:
                word = '{' + word + '}'
            bracketed_capitals_text.append(word)
        return ' '.join(bracketed_capitals_text)



