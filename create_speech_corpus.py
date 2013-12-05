"""
Create a corpus of speeches from seed links
"""


__author__ = 'Aaron'

# Import required modules
from bs4 import BeautifulSoup
import re
import urllib
import AlchemyAPI
import xml.etree.ElementTree as ET

def get_html_source(url):
    """Returns the html source of the page at url"""
    # import urllib
    try:
        sock = urllib.urlopen(url)
        html_source = sock.read()
        sock.close()
        return html_source
    except IOError:
        print "IOError: Not a valid URL"


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


def clean_text(some_text):
    # import re
    some_clean_text = re.sub(r'\n|\t', '', some_text)           # Remove new line and tabs
    some_clean_text = re.sub(' +', ' ', some_clean_text)        # Replace multiple spaces with one space
    return some_clean_text


def process_speech_source(url):
    # import AlchemyAPI
    try:
        # Create an AlchemyAPI object.
        alchemyObj = AlchemyAPI.AlchemyAPI()

        # Load the API key from disk.
        alchemyObj.loadAPIKey("api_key.txt")

        # Extract page text from a web URL (ignoring navigation links, ads, etc.).
        result = alchemyObj.URLGetText(url)

        speech_text = xml_to_text(result)
        speech_text = clean_text(speech_text)

    except TypeError:
        print "There is a TypeError in process_speech_source"

    return 1980, speech_text


def xml_to_text(text_xml):
    """Use xml.etree.ElementTree to return text from the AlchemyAPI text extraction output"""
    # import xml.etree.ElementTree as ET
    root = ET.fromstring(text_xml)
    return root.find('text').text


def get_corpus(seeds):
    # Extract links to speeches from "seeds". These links should be links to the text of actual speeches.
    speeches = []
    processed = []
    for seed in seeds:
        html = get_html_source(seed)
        speeches, processed = process_links(html, speeches, processed)

    return speeches


def main():
    seed = ["http://www.americanrhetoric.com/speechbanka-f.htm"]
    speeches = get_corpus(seed)
    print speeches


if __name__ == "__main__":
    main()
