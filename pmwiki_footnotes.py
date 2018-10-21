from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor
from markdown.treeprocessors import Treeprocessor
from markdown.util import etree
import pdb

footnote_pattern = r'\[\^((?:#[0-9]+(?: .+?)?)|@)\^\]'

class PmWikiFootnotes(Extension):
    
    def extendMarkdown(self, md, whoknows):
        md.registerExtension(self)
        md.inlinePatterns.register(FootnoteInlineProcessor(footnote_pattern,self),
                                   "PmWikiFootnoteInline",
                                   25)
        md.treeprocessors.register(FootnoteInjector(self),
                                   "PmWikiFootnoteInjector",
                                   0)
        self.reset()

    def add_footnote(self, number, text):
        self._notes[number] = text
        
    def add_citation(self, number):
        """Because citations are always monotonic starting at one we just have to 
        know how many there are to generate links to them for the footnote.

        number - The number of the *footnote* to increment citation count for."""
        try:
            self._citations[number] += 1
        except KeyError:
            self._citations[number] = 1

    def get_footnotes(self):
        """Return an ordered ascending iterable of footnotes."""
        return [(number, self._notes[number]) for number in self._notes.keys()]
            
    def get_auto_index(self):
        """Find the highest number in the footnote set and return its 1-increment."""
        numbers = list(self._notes.keys())
        numbers.sort()
        try:
            return numbers[-1] + 1
        except IndexError:
            return 1

    def get_citation_count(self, number):
        try:
            return self._citations[number]
        except IndexError:
            return 0
        
    def get_citation_index(self, number):
        """Return the 1-increment of the number of citations a footnote has."""
        try:
            return self._citations[number] + 1
        except KeyError:
            return 1
    
    def reset(self):
        self.note_count = 0
        self._notes = {}
        self._citations = {}

class FootnoteInjector(Treeprocessor):
    """Once the citations have been generated inline, we search for the instances
    of the footnotes div and populate them with collected footnotes."""
    def __init__(self, footnotes):
        super(FootnoteInjector, self).__init__()
        self.footnotes = footnotes

    def run(self, root):
        pdb.set_trace()
        footnote_divs = root.findall(".//div[@class='footnotes']")
        for footnote_div in footnote_divs:
            for footnote in self.footnotes.get_footnotes():
                fn_span = etree.SubElement(footnote_div, "p")
                fn_span.set("id", "fn{}-0".format(footnote[0]))
                fn_num = etree.SubElement(fn_span, "sup")
                fn_num.text = str(footnote[0])
                fn_num.tail = " ("
                citations = etree.SubElement(fn_span, "span")
                citations.set("class", "fn-backlinks")
                citations.tail = ") "
                for citation_i in range(self.footnotes.get_citation_count(footnote[0])):
                    citation_backl = etree.SubElement(citations, "a")
                    citation_backl.set("href", "#fn{}-{}".format(footnote[0],
                                                                citation_i + 1))
                    citation_backl.text = str(citation_i + 1) + " "
                fn_text = etree.SubElement(fn_span, "span")
                fn_text.text = str(footnote[1])
        return root
            
class FootnoteInlineProcessor(InlineProcessor):
    def __init__(self, pattern, footnotes):
        super(FootnoteInlineProcessor, self).__init__(pattern)
        self.footnotes = footnotes
        
    def handleMatch(self, match, full_text):
        """So the basic approach taken here is to replace footnotes in-text with 
        pointers to footnotes that are later injected into the bottom of the page.

        For example, the footnote [^#1^] could become <a href="#fn1-1"><sup>1</sup></a>.
        The format fn1-1 is used so that multiple citations of the same footnote can be 
        pointed to the same note. Each time a footnote is referenced the right numeral is 
        incremented by one. So if this is the 3rd reference to footnote one you 
        would get the output: <a href="#fn1-3"><sup>1</sup></a>; the reason for this
        is so that footnotes can point back to the places where they're cited even
        if that occurs multiple times in the text."""
        inner_text = match.groups()[0]
        if inner_text == "@":
            footnote_div = etree.Element("div")
            footnote_div.set("class", "footnotes")
            return footnote_div, match.start(0), match.end(0)
        # Handle footnotes
        elif len(inner_text.split()) > 1:
            pdb.set_trace()
            if inner_text.split()[0][0] == '#':
                number = inner_text.split()[0][1:]
                text = inner_text.split(maxsplit=1)[1]
                self.footnotes.add_footnote(number, text)
                # If this is a elaboration on citation don't want to cite twice
                if self.footnotes.get_citation_count(number):
                    return "", match.start(0), match.end(0)
                else:
                    footnote_number = number                
            else:
                number = self.footnotes.get_auto_index()
                self.footnotes.add_footnote(number, inner_text)
                footnote_number = number
        # Handle citations
        else:
            footnote_number = inner_text[1:]
            
        citation_index = self.footnotes.get_citation_index(footnote_number)
        citation = etree.Element('a')
        citation.set("id", "fn{}-{}".format(footnote_number, citation_index))
        citation.set("href", "fn{}-0".format(footnote_number))
        citation.text = str(footnote_number)
        self.footnotes.add_citation(footnote_number)
        return citation, match.start(0), match.end(0)
