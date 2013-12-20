"""
Create a corpus of speeches from seed links
"""


__author__ = 'Aaron'

# Import required modules
import re
from projectutils import get_datecode
from bs4 import BeautifulSoup
from projectutils import readobject, saveobject, get_html_source, clean_text
from projectutils import alchemy_page_text


def process_links(html):
    """
    Takes as input html that has links to speeches. Returns info on those speeches.

    input:
    html = page source that contains links to speeches

    output:
    dictionary speeches
    speeches.keys = url of speeches processed from input
    for each key the value pair is another dictionary containing:
        auth = author of speech
        date = year speech given
        text = text of speech

    * Only the links to speeches on AmericanRhetoric.com are processed
    """

    speeches = {}                                                       # Initialize speeches to empty dictionary
    try:                                                                # If this exists on disk read it in
        speeches = readobject("program_data_files/speeches")
    except IOError:
        print "speeches file not found on disk"

    alchemy_calls = {}                                                  # Need to track calls to alchemy api
    try:                                                                # Limit = 1000/day
        alchemy_calls = readobject("alchemy_calls")
    except IOError:
        print "file alchemy_calls not found on disk"
    date_key = get_datecode()
    if date_key not in alchemy_calls:
        alchemy_calls[date_key] = 0
    max_per_day = 1000

    # Initialize variables
    soup = BeautifulSoup(html)
    pattern = '^speeches'

    try:
        for link in soup.find_all('a'):
            url = unicode(link.get('href'))                             # Modified from str( to unicode(
            on_site = re.search(pattern, url)
            if on_site and alchemy_calls[date_key] < max_per_day:
                url = "".join(["http://americanrhetoric.com/", url])
                if url not in speeches.keys():
                    # Extract Author
                    text = "".join(link.stripped_strings)               # Merge all text into one string

                    # text = text.encode('utf-8')                       # TODO can I leave these out?
                    # text = text.encode('ascii', 'ignore')             # Convert text to straight ascii

                    auth = text.split(":")[0].rstrip()                  # Everything in front of : should be author
                                                                        # then remove whitespace
                    auth = clean_text(auth)                             # clean up auth

                    # Extract Speech text from url
                    alchemy_calls[date_key] += 1
                    text = alchemy_page_text(url)

                    # Extract date from url source
                    date = extract_date(url)

                    speeches[url] = {'auth': auth, 'date': date, 'text': text}
    finally:
        saveobject(speeches, "program_data_files/speeches")
    return speeches


def extract_date(url):
    html = get_html_source(url)
    # e.g. (delivered or broadcast) 21 September 2000
    pattern_dm = r'(delivered|broadcast)\s*\d*\s*\D*\s*(?P<year>[0-9]{4})'
    date = re.search(pattern_dm, html, re.IGNORECASE)
    if date is None:
        # e.g. (delivered or broadcast) September 21, 2000
        pattern_md = r'(delivered|broadcast)\s*\D*\s*\d*,*\s*(?P<year>[0-9]{4})'
        date = re.search(pattern_md, html, re.IGNORECASE)
    if date:
        return int(clean_text(date.group('year')))
    else:
        return None


def get_corpus(seeds):
    # Extract links to speeches from "seeds". These links should be links to the text of actual speeches.

    for seed in seeds:
        html = get_html_source(seed)
        speeches = process_links(html)

    return speeches


def main():
    seeds = ["http://www.americanrhetoric.com/speechbanka-f.htm"]
    speeches = get_corpus(seeds)
    print len(speeches)


if __name__ == "__main__":
    main()
