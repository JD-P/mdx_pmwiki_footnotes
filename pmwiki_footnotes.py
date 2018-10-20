from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor
from markdown.util import etree

footnote_pattern = r'\[\^((?:#[0-9]+(?: .+)?)|@)\^\]'

class PmWikiFootnotes(Extension):
    
    def extendMarkdown(self, md, whoknows):
        md.registerExtension(self)
        md.inlinePatterns.register(FootnoteInlineProcessor(footnote_pattern,self),
                                   "PmWikiFootnoteInline",
                                   25)
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

    def get_auto_index(self):
        """Find the highest number in the footnote set and return its 1-increment."""
        numbers = list(self._notes.keys())
        numbers.sort()
        try:
            return numbers[-1] + 1
        except IndexError:
            return 1

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
            return footnote_div
        # Handle footnotes
        elif len(inner_text.split()) > 1:
            if inner_text.split()[0][0] == '#':
                number = inner_text.split()[0][1:]
                text = inner_text.split(maxsplit=1)[1]
                self.footnotes.add_footnote(number, text)
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
        self.footnotes.add_citation(footnote_number)
        return citation, match.start(0), match.end(0)
