"""
Various utilities needed in project

saveobject: save object to disk
readobject: read object from disk
get_html_source: get page source
"""
import re
import urllib
import AlchemyAPI
import cPickle as pickle
import xml.etree.ElementTree as ET
from datetime import datetime
import sys

__author__ = 'Aaron'

def saveobject(obj, filename):
    # import cPickle as pickle
    with open(filename, 'wb') as output:
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)


def readobject(filename):
    # import cPickle as pickle
    with open(filename, 'rb') as input_file:
        return pickle.load(input_file)


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


def alchemy_page_text(url):
    # import AlchemyAPI
    try:
        # Create an AlchemyAPI object.
        alchemyObj = AlchemyAPI.AlchemyAPI()

        # Load the API key from disk.
        alchemyObj.loadAPIKey("api_key.txt")

        # Extract page text from a web URL (ignoring navigation links, ads, etc.).
        result = alchemyObj.URLGetText(url)

        text = xml_to_text(result)
        text = clean_text(text)

        return text

    except TypeError:
        return "There is a TypeError in alchemy_page_text"


def xml_to_text(xml_string, node_name='text'):
    """Use xml.etree.ElementTree to return text from the AlchemyAPI text extraction output"""
    # import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_string)
    return_string = u""
    for node in root.iter(node_name):
        if node.text is None:
            pass
        else:
            return_string = u"".join([return_string, unicode(node.text)])
    return return_string


def clean_text(some_text):
    # import re
    some_clean_text = re.sub(r'\n|\t', '', some_text)           # Remove new line and tabs
    some_clean_text = re.sub(' +', ' ', some_clean_text)        # Replace multiple spaces with one space
    return some_clean_text


def alchemy_keywords(text):
    """Use the AlchemyAPI module to get a list of keywords from text"""
    if text:
        # TODO Alchemy API breaks if overview text is greater than 150 kbytes
        # First step skip these. If time look at truncating, splitting, or combining
        # by first skipping, I will be easier to update later
        if sys.getsizeof(text) > 150000:
            return {}

        # Create an AlchemyAPI object.
        alchemy_obj = AlchemyAPI.AlchemyAPI()

        # Load the API key from disk.
        alchemy_obj.loadAPIKey("api_key.txt")

        # Extract topic keywords from a text string.
        result = alchemy_obj.TextGetRankedKeywords(text)

        root = ET.fromstring(result)

        keyword_dictionary = {}

        for node in root.iter("keyword"):
            keyword = node.find("text").text.encode("utf-8")
            relevance = float(node.find("relevance").text)
            keyword_dictionary[keyword] = relevance

        return keyword_dictionary
    else:
        print "No text to analyze"
        return {}


def get_datecode():
    now = datetime.utcnow()
    return now.strftime("%Y%m%d")


def main():
    pass


if __name__ == "__main__":
    main()