"""
Create a corpus of speeches from seed links
"""


__author__ = 'Aaron'

# Import required modules
import re
from projectutils import get_datecode
from bs4 import BeautifulSoup
from projectutils import readobject, saveobject, get_html_source, clean_text
from projectutils import alchemy_page_text, alchemy_keywords


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

    # There seems to be a few broken links on the web site that result in error 404 pages
    # I'm sure there is a way to catch these and skip them but for now there aren't many
    # and this works.
    broken_links = ['http://americanrhetoric.com/speeches/gwbreagansdeath.htm',
                    'http://americanrhetoric.com/speeches/joachimgauckinauguraladdressgerman.htm',
                    'http://americanrhetoric.com/speeches/johnleibowitzpathsettlement.htm',
                    'http://americanrhetoric.com/speeches/robertsloanbayloruniversity.htm',
                    'http://americanrhetoric.com/speeches/tdjakesseedonmyside.html']

    alchemy_calls = {}                                     # Need to track calls to alchemy api
    try:                                                   # Limit = 1000/day
        alchemy_calls = readobject("alchemy_calls")
    except IOError:
        print "file alchemy_calls not found on disk"
    date_key = get_datecode()
    if date_key not in alchemy_calls:
        alchemy_calls[date_key] = 0
    max_per_day = 1000

    # Initialize variables
    soup = BeautifulSoup(html)
    pattern = '^speeches'               # I want to follow every link that begins with speeches
    need_save = False                   # Save flag so I'm only saving when necessary

    try:
        for link in soup.find_all('a'):
            url = unicode(link.get('href'))
            on_site = re.search(pattern, url)
            if on_site and alchemy_calls[date_key] < max_per_day:
                url = "".join(["http://americanrhetoric.com/", url])
                if url not in speeches.keys() and url not in broken_links:
                    print "processing url: {0}".format(url)
                    # Extract Author
                    auth = "".join(link.stripped_strings)               # Merge all text into one string

                    auth = auth.split(":")[0].rstrip()                  # Everything in front of : should be author
                                                                        # then remove whitespace
                    auth = clean_text(auth)                             # clean up auth

                    # Extract date from url source
                    date = extract_date(url)

                    # Extract Speech text from url
                    alchemy_calls[date_key] += 1
                    text = alchemy_page_text(url)

                    # Extract Keywords from speech text
                    keywords = alchemy_keywords(text.encode("utf-8"))

                    need_save = True
                    speeches[url] = {'auth': auth, 'date': date, 'text': text, 'keywords': keywords}

    except 'Error making API call':
        # FIXME: this isn't catching anything
        print 'Caught exception "Error making API call" from Alchemy API'

    finally:
        if need_save:
            print "alchemy calls for today = {0}".format(alchemy_calls[date_key])
            print "saving objects: speeches, alchemy_calls"
            saveobject(speeches, "program_data_files/speeches")
            saveobject(alchemy_calls, "alchemy_calls")
        else:
            print "no modifications to speeches"
    return speeches


def extract_date(url):
    """
    Most speeches on American Rhetoric have one of the phrases described below containing the date

    If found, returns year as int, otherwise returns None
    """
    html = get_html_source(url)
    pattern_dm = r'(delivered|broadcast)\s*\d*\s*\D*\s*(?P<year>[0-9]{4})'
                    # e.g. (delivered or broadcast) 21 September 2000
    date = re.search(pattern_dm, html, re.IGNORECASE)
    if date is None:
        pattern_md = r'(delivered|broadcast)\s*\D*\s*\d*,*\s*(?P<year>[0-9]{4})'
                        # e.g. (delivered or broadcast) September 21, 2000
        date = re.search(pattern_md, html, re.IGNORECASE)
    if date:
        return int(clean_text(date.group('year')))
    else:
        return None


def summarize(speeches):
    summary = dict()
    missing_year_count = 0
    for key in speeches.keys():
        try:
            summary[key] = dict(year=int(speeches[key]['date']), keywords=speeches[key]['keywords'])
        except TypeError:
            # To debug, uncomment the following 2 lines
            #print "create_speech_corpus.summarize: no year. Skipping speech by {0}"\
            #    .format(speeches[key]['auth'])
            missing_year_count += 1
    if missing_year_count > 0:
        print "create_speech_corpus.summarize: {0} speeches were skipped due to missing year"\
            .format(missing_year_count)
    return summary


def get_corpus(seeds):
    # Extract links to speeches from "seeds". These links should be links to the text of actual speeches.

    for seed in seeds:
        html = get_html_source(seed)
        speeches = process_links(html)

    # This is the final output of this module.
    # summary is a dictionary containing year and keywords for each speech
    summary = summarize(speeches)

    return summary


def main():
    seeds = ["http://www.americanrhetoric.com/speechbanka-f.htm",
             "http://www.americanrhetoric.com/speechbankg-l.htm",
             "http://www.americanrhetoric.com/speechbankm-r.htm",
             "http://www.americanrhetoric.com/speechbanks-z.htm"]
    summary = get_corpus(seeds)

    print "Number of summarized speeches = {0}".format(len(summary))


if __name__ == "__main__":
    main()
