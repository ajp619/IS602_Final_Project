"""
Create a corpus of speeches from seed links
"""


__author__ = 'Aaron'

# Import required modules
import re
import AlchemyAPI
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup

from projectutils import readobject, saveobject, get_html_source, clean_text
from projectutils import alchemy_page_text


def process_links(html, return_list, processed):
    # Return a list of authors and links from an AmericanRhetoric.com page
    # that point to a speech also on AmericanRhetoric

    # Import
    # from bs4 import BeautifulSoup
    # import re

    # Initialize variables
    soup = BeautifulSoup(html)
    pattern = '^speeches'

    for link in soup.find_all('a'):
        url = str(link.get('href'))
        on_site = re.search(pattern, url)
        if on_site:
            url = "".join(["http://americanrhetoric.com/", url])
            if url not in processed:
                # Extract Author
                text = "".join(link.stripped_strings)           # Merge all text into one string
                text = text.encode('ascii', 'ignore')           # Convert text to straight ascii
                auth = text.split(":")[0].rstrip()              # Everything in front of : should be author
                                                                # then remove whitespace
                auth = clean_text(auth)                         # clean up auth

                # Extract Date and Speech from url
                date, text = process_speech_source(url)

                return_list.append([auth, date, text])
                processed.append(url)
    return return_list, processed


def process_speech_source(url):
    speech_text = alchemy_page_text(url)

    return 1980, speech_text


def get_corpus(seeds):
    # Extract links to speeches from "seeds". These links should be links to the text of actual speeches.
    speeches = []
    processed = []

    try:
        readobject("speeches")
        readobject("processed")
    except IOError:
        print "file not found"

    for seed in seeds:
        html = get_html_source(seed)
        speeches, processed = process_links(html, speeches, processed)

    saveobject(speeches, "speeches")
    saveobject(processed, "processed")
    return speeches


def main():
    seed = ["http://www.americanrhetoric.com/speechbanka-f.htm"]
    speeches = get_corpus(seed)
    print speeches


if __name__ == "__main__":
    main()
