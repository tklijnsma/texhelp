import re, logging, sys

class Helper(object):
    """docstring for Helper"""
    def __init__(self, tex_file=None):
        super(Helper, self).__init__()
        self.tex_file = tex_file
        if not self.tex_file is None:
            self.read()
        self.comments_removed = False
        
    def read(self):
        with open(self.tex_file, 'r') as tex_fp:
            self.tex_text = tex_fp.read()

    def remove_all_text_after_comments(self):
        if self.comments_removed:
            logging.debug('Comments already removed')
            return
        commentless_text = []
        for line in self.tex_text.split('\n'):
            commentless_text.append(line)
        self.tex_text = '\n'.join(commentless_text)
        self.comments_removed = True

    def remove_commented_part_from_line(self, line):
        logging.debug('Removing possible comment from {0}'.format(line))
        match = re.search(r'(.*[^\\])%', line)
        if match:
            line = match.group(1)
            logging.debug('Found match')
        else:
            logging.debug('No match found')
        logging.debug('Returning {0}'.format(line))
        return line            

    def print_cites(self):
        citations, citation_counts = self.get_cites(self.tex_text)
        for i_citation, citation in enumerate(citation_counts):
            s = '[{0}] {1}'.format(i_citation, citation)
            count = citation_counts[citation]
            if count > 1:
                s += ' ({0} times)'.format(count)
            print s

    def get_cites(self, text):
        self.remove_all_text_after_comments()
        cite_pat = r'\\cite\{(.*?)\}'
        citations = []
        citation_counts = {}
        for cite_match in re.findall(cite_pat, text):
            for citation in cite_match.split(','):
                citation = citation.strip()
                if not citation in citations:
                    citations.append(citation)
                    citation_counts[citation] = 1
                else:
                    citation_counts[citation] += 1
        return citations, citation_counts

    def merge_cites(self, old_citations, old_citation_counts, new_citations, new_citation_counts):
        for new_citation in new_citations:
            if new_citation in old_citations:
                old_citation_counts[new_citation] += new_citation_counts[new_citation]
            else:
                old_citations.append(new_citation)
                old_citation_counts[new_citation] = new_citation_counts[new_citation]
        return old_citations, old_citation_counts

    def print_inputs(self, inputs=None):
        if inputs is None: inputs = self.get_inputs()
        for inp in inputs:
            print inp

    def get_inputs(self):
        return self.get_inputs_from_text(self.tex_text)

    def get_inputs_from_text(self, text):
        input_pat = r'\n(.*?)\\input\{(.*?)\}'
        inputs = []
        for possible_comment, inp in re.findall(input_pat, text):
            if '%' in possible_comment:
                continue
            inputs.append(inp)
        return inputs

    def get_images(self):
        return self.get_images_from_text(self.tex_text)

    def get_images_from_text(self, text):
        img_pat = r'\n(.*?)\\includegraphics\[.*?\]\{(.*?)\}'
        imgs = []
        for possible_comment, img in re.findall(img_pat, text):
            if '%' in possible_comment:
                continue
            imgs.append(img)
        return imgs

    def print_images(self, imgs=None):
        if imgs is None: imgs = self.get_images()
        for img in imgs:
            print img

    def get_figures(self):
        fig_pat = r'\n(.*?)\\begin\{figure\}([\w\W]*?)\\end\{figure\}'
        figs = []
        for possible_comment, fig in re.findall(fig_pat, self.tex_text):
            if '%' in possible_comment: continue
            figs.append(fig)

        caption_pat = r'\\caption\{([\w\W]*\})' # greedy match; undo later
        label_pat = r'\\label\{(.*?)\}'

        results = []
        for fig in figs:
            imgs = self.get_images_from_text(fig)
            
            caption_match = re.search(caption_pat, fig)
            if not caption_match:
                logging.error('No caption found')
                caption = 'None'
            else:
                caption = caption_match.group(1)
                caption = self.find_text_within_closing_brackets(caption)

            label_match = re.search(label_pat, fig)
            if not label_match:
                logging.error('No label found')
                label = 'None'
            else:
                label = label_match.group(1)

            result = {
                'imgs' : imgs,
                'caption' : caption,
                'label' : label
                }
            results.append(result)
        return results

    def print_figures(self, figs=None, print_captions=False):
        if figs is None: figs = self.get_figures()
        for fig in figs:
            print 'Figure label {0}:'.format(fig['label'])
            print '  ' + '\n  '.join(fig['imgs'])
            if print_captions:
                print '  caption:\n    {0}'.format(fig['caption'])

    def find_text_within_closing_brackets(self, text, b='{', e='}', start_index=0):
        level = 0
        if not(start_index == 0):
            text = text[start_index:]

        for i, c in enumerate(text):
            if c == e:
                if level == 0:
                    break
                else:
                    level -= 1
            if c == b:
                level += 1
        else:
            logging.error('Could not find closing bracket {0}')

        r = text[:i]
        logging.debug('Found following text within brackets: %s' % r)
        return r

