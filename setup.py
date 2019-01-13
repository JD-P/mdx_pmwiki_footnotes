from setuptools import setup, find_packages

setup(
    name="mdx-pmwiki-footnotes",
    version="0.1",
    install_requires=['Markdown>=2.6.11'],
    author="John David Pressman",
    author_email="jd@jdpressman.com",
    description=("Markdown extension which implements PmWiki footnote syntax. "
                 "See https://wiki.obormot.net/Blog/FeatureUpdateFootnotes for "
                 "more information."),
    license="MIT",
    url="https://github.com/JD-P/mdx_pmwiki_footnotes/")
