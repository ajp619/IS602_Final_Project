"""
Various utilities needed in project
"""
import re
import urllib
import AlchemyAPI
import cPickle as pickle
import xml.etree.ElementTree as ET
from datetime import datetime
import sys
from matplotlib.rcsetup import validate_fontsize
import numpy as np
import matplotlib.pyplot as plt

__author__ = 'Aaron'


def saveobject(obj, filename):
    """Shortcut to save file"""
    # import cPickle as pickle
    with open(filename, 'wb') as output:
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)


def readobject(filename):
    """Shortcut to read file"""
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
    """
    Tool from AlchemyAPI to extract main text from web page

    Used here to extract speech text from americanrhetoric.com
    """
    # import AlchemyAPI
    try:
        # Create an AlchemyAPI object.
        alchemyObj = AlchemyAPI.AlchemyAPI()

        # Load the API key from disk.
        alchemyObj.loadAPIKey("api_key.txt")

        # Extract page text from a web URL (ignoring navigation links, ads, etc.).
        result = alchemyObj.URLGetText(url)

        # Result returned in xml format with node 'text' containing the text
        text = xml_to_text(result)
        # remove new lines, tabs, and whitespace
        text = clean_text(text)

        return text

    except TypeError:
        return "There is a TypeError in alchemy_page_text"


def xml_to_text(xml_string, node_name='text'):
    """
    Use xml.etree.ElementTree to return text from any node named <node_name>

    Used in AlchemyAPI text extraction output
    Also use to process 'Overview' nodes in xml file from thetvdb.com
    """
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
    """
    Remove new lines, tabs, and whitespace from text blob
    """
    # import re
    some_clean_text = re.sub(r'\n|\t', '', some_text)           # Remove new line and tabs
    some_clean_text = re.sub(' +', ' ', some_clean_text)        # Replace multiple spaces with one space
    return some_clean_text


def alchemy_keywords(text):
    """Use the AlchemyAPI module to get a list of keywords from text"""
    if text:
        # TODO Alchemy API breaks if overview text is greater than 150 kbytes
        # First step skip these. If time look at truncating, splitting, or combining
        # by first skipping, it will be easier to update later
        if sys.getsizeof(text) > 150000:
            return {}

        # Create an AlchemyAPI object.
        alchemy_obj = AlchemyAPI.AlchemyAPI()

        # Load the API key from disk.
        alchemy_obj.loadAPIKey("api_key.txt")

        # Extract topic keywords from a text string.
        result = alchemy_obj.TextGetRankedKeywords(text)

        # Use xml.etree.ElementTree to process xml returned from AlchemyAPI
        # extract keyword and relevance
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
    """
    Return a datecode in UTC time
    """
    now = datetime.utcnow()
    return now.strftime("%Y%m%d")


def dict_by_year(incoming_dict):
    """
    Convert a dictionary organized by keywords to a dictionary organized by year

    Input:
        expects incoming_dictionary in format:
            {key: {'year': YYYY, 'keywords':{'word': value}, ...}}
    Output:
        returns dictionary in format:
            {year as key: {word: relevance}}
    --------
    Note: I have chosen to add relevance for repeating words. The choice of how repeating words
        are handled will influence the final results.
    """
    by_year = {}
    for key in incoming_dict.keys():
        try:
            year = incoming_dict[key]['year']
            keywords = incoming_dict[key]['keywords']
            for word in keywords:
                if year in by_year.keys():
                    if word in by_year[year].keys():
                        by_year[year][word] += keywords[word]
                    else:
                        by_year[year][word] = keywords[word]
                else:
                    by_year[year] = {word: keywords[word]}
        except KeyError:
            print "KeyError in dict_by_year. Key = {0}".format(key)
    return by_year


def sort_dict_keys_by_values(dict):
    """
    Return a list of keywords sorted by their values

    Input:
        dictionary(key: numerical value)
    Output:
        list
    """
    return sorted(dict.keys(), key=lambda x: dict[x], reverse=True)


def create_heat_map(source, response, max_keywords, start_year, interval):
    """
    Create a heat map from two dictionaries.

    Input:
        Source dictionary contains keywords by year and is used to extract a list of sorted
            words for start_year = sorted_words - set to length of max_keywords
        Response dictionary contains keywords by year and is used to return an intensity value
            for each year in the range (start_year + interval) for each of the keywords found
            in sorted_words
    Output:
        Heat map: numpy array with intensity values
    --------

    """
    # Convert source dictionary, which is organized by keywords, to source_by_year dictionary
    # which is organized by year
    source_by_year = dict_by_year(source)
    # Same conversion for response dictionary
    response_by_year = dict_by_year(response)

    # Initialize heat map array
    heat_map = np.zeros((max_keywords, interval))

    # get list of sorted words from source. The intensity of these words will be
    # measured in the resonse dictionary and returned in the heat map
    sorted_words = sort_dict_keys_by_values(source_by_year[start_year])

    # c= column, r=row in heat map
    for c in range(interval):
        year = start_year + c
        for r in range(max_keywords):
            # sorted_words might not have as many keywords as max_keywords
            # if not leave it as zero (initialized above)
            if r < len(sorted_words):
                word = sorted_words[r]
                try:
                    value = response_by_year[year][word]
                except KeyError:                            # The keyword in sorted_words may not exist
                    value = 0                               # in the response keywords for year
                finally:
                    heat_map[r, c] = value
    return heat_map, sorted_words


def plot_heat_map(heat_map, keywords, start_year):
    # modeled after http://matplotlib.org/examples/color/colormaps_reference.html
    nrows, ncols = heat_map.shape
    fig, axes = plt.subplots(nrows=nrows)
    fig.subplots_adjust(top=0.92, bottom=0.05, left=0.2, right=0.99)
    axes[0].set_title('Intensity of words and phrases found in television shows from ' +
                      str(start_year) +
                      '\nas they occur in political speeches over time',
                      fontsize=12)

    for ax, name, usage in zip(axes, keywords, heat_map):
        usage = np.vstack((usage, usage))
        ax.imshow(usage, aspect='auto', cmap=plt.get_cmap('Blues'))
        pos = list(ax.get_position().bounds)
        x_text = pos[0] - 0.01
        y_text = pos[1] + pos[3]/2.
        fig.text(x_text, y_text, name, va='center', ha='right', fontsize=8)

    # Turn off all y axis information.
    for i, ax in list(enumerate(axes)):
        # ax.set_axis_off()
        ax.get_yaxis().set_visible(False)                                   # Remove y axis information
        ax.set_xticklabels(())                                              # Remove x tick labels
        ax.xaxis.set_ticks(range(0, ncols, 2))                              # Set x tick label range
        # Now for only the last plot at the bottom:
        if i == len(axes) - 1:
            # ax.xaxis.set_ticks(range(0, ncols, 2)) # This was here when output generated but I think it's unnecessary
            ax.set_xticklabels((range(start_year, start_year + ncols, 2)))  # Show years for x tick labels
            ax.tick_params(axis='x', labelsize=8)                           # Set font size for x ticks
    return fig


def main():
    pass


if __name__ == "__main__":
    main()