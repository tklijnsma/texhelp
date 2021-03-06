# -*- coding: utf-8 -*-

import texhelp
import logging
import re


class BibFormatter(object):
    """docstring for BibFormatter"""

    def __init__(self, cms_style=True):
        super(BibFormatter, self).__init__()
        self.cms_style = cms_style

    def get_citation(self, raw):
        try:
            citation = BibCitation(raw)
            citation.get_entry_type()
            citation.read_fields()
            if self.cms_style: citation.format_cms_style()
            return citation
        except:
            logging.error('Encountered error for the following raw text:\n' + raw)
            raise



class BibCitation(object):
    """docstring for BibCitation"""
    def __init__(self, raw):
        super(BibCitation, self).__init__()
        self.raw = raw
        self.citename = ''
        self.fields = {}
        self.keys = []

    def get_entry_type(self):
        raw = self.raw.strip()
        if not raw.startswith('@'): raise ValueError('Unexpected bib format: Does not start with \'@\'')
        match = re.match(r'@(\w+)\{', raw)
        open_tag = match.group()
        self.entry_type = match.group(1)
        if not raw.endswith('}'): raise ValueError('Unexpected bib format: Does not end with \'}\'')
        self.bib = raw[len(open_tag):-1]

    def comma_separate_ignoring_quotes(self, text):
        # Flatten line breaks
        text = text.replace('\n','')
        quote_mode = False
        separated = []
        field = ''
        for i, c in enumerate(text):
            if c == '"':
                if i>0 and text[i-1] == '\\':
                    field += c
                else:
                    quote_mode = not(quote_mode)
                    field += c
            elif c == ',' and not(quote_mode):
                separated.append(field)
                field = ''
            else:
                field += c
        if text[-1] != ',': separated.append(field)
        return separated

    def interpret_raw_field(self, raw_field):
        if not '=' in raw_field:
            raise ValueError(
                'Cannot interpret the following raw field: {0}'.format(raw_field)
                )
        raw_key, raw_val = raw_field.split('=',1)
        key = raw_key.strip().strip('"').strip().lower()
        val = raw_val.strip().strip('"').strip()
        val = re.sub(r' +', ' ', val)
        val = val.decode('utf-8')
        val = val.replace(u'\xa0', u' ') # Ignore non-breaking spaces
        # # There may still be some characters in these strings 
        # logging.debug('Test log: val = ')
        # try:
        #     logging.debug(val.encode('utf-8'))
        # except UnicodeEncodeError:
        #     print 'Problem with key {0}:'.format(key)
        #     print val
        #     raise
        return key, val

    def read_fields(self):
        # First read the citename
        self.citename, bib = self.bib.split(',', 1)
        self.citename = self.citename.strip()
        
        if bib.strip().endswith(','):
            logging.warning(
                'It looks like the last field of citation {0} ends'
                ' with a comma; the last field should not have one!'
                .format(self.citename)
                )

        for raw_field in self.comma_separate_ignoring_quotes(bib):
            key, val = self.interpret_raw_field(raw_field)
            self.fields[key] = val
            self.keys.append(key) # Also keep a sorted list of the keys
            logging.debug('key/val: {0:12} = {1}'.format(key, val.encode('utf-8')))

    def remove_key(self, key):
        del self.fields[key]
        self.keys.remove(key)

    def format_cms_style(self):
        cmsformatter = CMSCiteFormatter(self.entry_type, self.fields, self.keys)
        cmsformatter.check_fields()
        self.entry_type = cmsformatter.entry_type
        self.fields = cmsformatter.fields
        self.keys = cmsformatter.keys

    def parse(self):
        out = []
        out.append('@{0}{{{1},'.format(self.entry_type, self.citename))
        capitalization_exceptions = {
            'archiveprefix' : 'archivePrefix',
            'primaryclass'  : 'primaryClass',
            'reportnumber'  : 'reportNumber',
            'slaccitation'  : 'SLACcitation',
            }
        max_key_length = max(map(len, self.keys))
        loop_keys = [k for k in self.keys if not k == 'rawtitle']
        for key in loop_keys:
            out.append(
                '    {0:{max_key_length}} = "{1}"{2}'
                .format(
                    capitalization_exceptions.get(key,key), self.fields[key].encode('utf-8'),
                    ',' if key != loop_keys[-1] else '',
                    max_key_length=max_key_length
                    )
                )
        out.append('    }')
        r = '\n'.join(out)
        is_ascii = all(ord(char) < 128 for char in r)
        if not(is_ascii):
            logging.error('The parsed output is NOT fully ASCII!')
        return r


class CMSCiteFormatter(object):
    """docstring for CMSCiteFormatter"""

    def __init__(self, entry_type, fields, keys=None):
        super(CMSCiteFormatter, self).__init__()
        self.entry_type = entry_type
        self.fields = fields
        if keys is None:
            self.keys = self.fields.keys()
        else:
            self.keys = keys
        self._is_a_pas = None

        self.err_msgs = []
        self.warning_msgs = []

    def error(self, msg):
        logging.error(msg)
        self.err_msgs.append(msg)

    def warning(self, msg):
        logging.warning(msg)
        self.warning_msgs.append(msg)

    def remove_key(self, key):
        del self.fields[key]
        self.keys.remove(key)

    def is_a_pas(self):
         if self._is_a_pas is None:
             self._is_a_pas = False
             for key in [ 'number', 'reportNumber' ]:
                 if key in self.keys:
                     if 'cms-pas' in self.fields[key].lower():
                         self._is_a_pas = True
                         break
             else:
                 if 'type' in self.keys:
                     if 'CMS Physics Analysis Summary' in self.fields['type']:
                         self._is_a_pas = True
         return self._is_a_pas

    def check_fields(self):
        if not 'year' in self.fields:
            self.error('year field not given')

        if 'href' in self.keys:
            self.error(
                'Found key \'href\' (=\"{1}\"), which should probably be replaced by \'url\''
                .format(self.fields['href'])
                )
        
        if 'pages' in self.keys and '-' in self.fields['pages']:
            self.warning('Correcting a range of pages: \"{0}\"'.format(self.fields['pages']))
            self.fields['pages'] = self.fields['pages'].split('-')[0].strip()
        
        if 'doi' in self.keys and 'url' in self.keys:
            self.warning('Found a url key even though a doi is specified; Removing key url')
            self.remove_key('url')
        if not 'doi' in self.keys:
            self.warning('No doi field found')
        
        if 'collaboration' in self.keys:
            if 'collaboration' in self.fields['collaboration'].lower():
                self.error(
                    'Found keyword \'collaboration\' in collaboration field,'
                    ' this should probably be removed: \"{0}\"'
                    .format(self.fields['collaboration'])
                    )

        if self.is_a_pas():
            if not 'type' in self.keys:
                self.warning('Is a PAS, but no field \'type\' found. Adding type manually.')
                self.keys.append('type')
                self.fields['type'] = '{CMS Physics Analysis Summary}'

            if self.entry_type != '@techreport{':
                self.warning('Is a PAS, but not a @techreport. Chaning entry_type to techreport')
                self.entry_type = '@techreport{'

            if not 'number' in self.keys:
                if 'reportNumber' in self.keys:
                    self.warning(
                        'Found no key \'number\', but found \'reportNumber\'; using that instead'
                        )
                    self.keys.append('number')
                    self.fields['number'] = self.fields['reportNumber']
                    self.remove_key('reportNumber')
                else:
                    self.error(
                        'No key \'number\' or \'reportNumber\'; \'number\' should be specified!'
                        )

        if not 'title' in self.keys:
            self.error('Found no key \'title\'.')
        else:
            optimized_title = self.get_reinterpreted_title(self.fields['title'])
            if not self.fields['title'] == optimized_title:
                logging.warning(
                    'Replacing title:\n'
                    'Old: \"{0}\"\nNew: \"{1}\"'
                    .format(self.fields['title'].encode('utf-8'), optimized_title.encode('utf-8'))
                    )
                if not 'rawtitle' in self.keys:
                    self.keys.append('rawtitle')
                    self.fields['rawtitle'] = self.fields['title']
                self.fields['title'] = optimized_title

        if 'journal' in self.keys and 'volume' in self.keys:
            match = re.match(r'([a-zA-Z])', self.fields['volume'][0])
            if match:
                vol_letter = match.group(1)
                new_journal_name = self.fields['journal'].strip() + ' ' + vol_letter.upper()
                self.warning(
                    'Detected a volume starting with a letter: {0}; '
                    'changing journal from "{1}" to "{2}"'
                    .format(self.fields['volume'], self.fields['journal'], new_journal_name)
                    )
                self.fields['journal'] = new_journal_name
                self.fields['volume'] = self.fields['volume'][1:]

        if 'number' in self.keys and not self.is_a_pas():
            logging.warning('Removing \'number\' key: {0}'.format(self.fields['number']))
            self.remove_key('number')

        if 'type' in self.keys:
            if not(self.fields['type'].startswith('{')):
                self.warning('Adding opening bracket to type field')
                self.fields['type'] = '{' + self.fields['type']
            if not(self.fields['type'].endswith('}')):
                self.warning('Adding closing bracket to type field')
                self.fields['type'] += '}'

        if 'collaboration' in self.keys:
            if 'atlas' in self.fields['collaboration'].lower() and 'cms' in self.fields['collaboration'].lower():
                self.warning(
                    'Detected ATLAS and CMS in the collaboration field; '
                    'Putting \'{ATLAS and CMS Collaborations}\' in the '
                    'author field instead.'
                    )
                if not 'author' in self.keys: self.keys.append('author')
                self.fields['author'] = '{ATLAS and CMS Collaborations}'
                self.remove_key('collaboration')


    def get_reinterpreted_title(self, raw):
        segments = raw.split('$')
        add_brackets = lambda text: '{' + text + '}'
        for i_segment in xrange(0,len(segments),2):
            segment = segments[i_segment]
            segment = segment.replace('{','').replace('}','').strip()
            new_segment = []
            words = segment.split(' ')
            for word in words:
                word = word.strip()
                if len(word) == 0:
                    pass
                elif not(re.search(r'[a-zA-Z]+', word)):
                    # Word fully composed of non-letter character
                    # word = add_brackets(word)
                    pass
                elif word == word.capitalize() and not word.isdigit():
                    # if word != words[0]:
                    #     word = add_brackets(word[0].upper()) + word[1:]
                    # 27-11: Realized CMS convention is actually lower case letters
                    if word != words[0]:
                        word = word.lower()
                        if word.strip() in ['higgs' ]:
                            word = add_brackets(word[0].upper()) + word[1:]
                elif word.lower() != word:
                    word = add_brackets(word)
                new_segment.append(word)
            segments[i_segment] = ' ' + ' '.join(new_segment)

        logging.debug('segments: {0}'.format(segments))

        # Re-concatenate
        math_mode = False
        out = u''
        for segment in segments:
            out += segment
            if math_mode:
                out += '$}'
            else:
                out += ' {$'
            math_mode = not(math_mode)

        if out.endswith(' {$'):
            out = out[:-3]

        out = re.sub(r' +', ' ', out)
        return out.strip()












