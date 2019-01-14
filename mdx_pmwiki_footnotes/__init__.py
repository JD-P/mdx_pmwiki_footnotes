from .pmwiki_footnotes import PmWikiFootnotes

def makeExtension(**kwargs):
    return PmWikiFootnotes(**kwargs)
