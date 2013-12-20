"""
Create corpus of tv shows from thetvdb.com
"""

__author__ = 'Aaron'

from urllib import quote_plus, urlopen
from projectutils import xml_to_text, readobject, saveobject
from projectutils import alchemy_keywords, get_datecode
import unirest
import re
from StringIO import StringIO
from zipfile import ZipFile
from contextlib import closing
import time


def construct_search_url(year):
    search_url = ["http://thetvdb.com/index.php?",
              "seriesname=",
              "&fieldlocation=2",
              "&language=7",
              "&genre=",
              "&year=", str(year),                       # want to loop through this one: 1940 - 2013
              "&network=",
              "&zap2it_id=&",
              "tvcom_id=",
              "&imdb_id=",
              "&order=translation",
              "&addedBy=",
              "&searching=Search",
              "&tab=advancedsearch"]
    return "".join(search_url)


def construct_mashape_query(search_url):
    query_url = ["https://crawlera.p.mashape.com/fetch?url=",
                 quote_plus(search_url),
                 "&data=%3Cdata%3E"]
    return "".join(query_url)


def get_info_from_response(html):
    pattern = ['<tr>'													    # Begin table row
               '<td class=".*?">.*?</td>'									# Row Number
               '<td class=".*?"><a.*?id=(.*?)\&amp;.*?>(.*?)</a></td>'      # Series Information: (id), (title)
               '<td class=".*?">.*?</td>'                                   # Genre
               '<td class=".*?">.*?</td>'                                   # Status
               '<td class=".*?">.*?</td>'                                   # Language
               '<td class=".*?">(.*?)</td>'                                 # (Network)
               '<td class=".*?">.*?</td>'                                   # ?
               '<td class=".*?">.*?</td>'                                   # ?
               '</tr>']                                                     # End table row
    pattern = pattern[0]

    regex = re.compile(pattern)
    return regex.findall(html)


def get_tv_shows(year_range, networks):

    tv_shows = []
    try:
        tv_shows = readobject("program_data_files/tv_shows_basic")
    except IOError:
        print "file: tv_shows_basic not found"

    years_already_processed = []
    try:
        years_already_processed = readobject("program_data_files/years_already_processed")
    except IOError:
        print "file: years_already_processed not found"

    mashape_calls = {}
    try:
        mashape_calls = readobject("mashape_calls")
    except IOError:
        print "file: mashape_calls not found"
    date_key = get_datecode()
    if date_key not in mashape_calls:
        mashape_calls[date_key] = 0
    max_per_day = 20

    mashape_key = readobject("mashape_key")

    try:
        for year in year_range:
            if year not in years_already_processed and mashape_calls[date_key] < max_per_day:
                print "processing {0}".format(year)
                search_url = construct_search_url(year)
                mashape_query = construct_mashape_query(search_url)
                mashape_header = {"X-Mashape-Authorization": mashape_key}
                try:
                    mashape_calls[date_key] += 1
                    response = unirest.get(mashape_query, headers=mashape_header)
                    years_already_processed.append(year)
                except ssl.SSLError as e:
                    if e.message == 'The read operation timed out':
                        response = None
                    else:
                        raise
                if response is not None:
                    response_items = get_info_from_response(response.body)  # = id, title, network
                    for item in response_items:
                        item_id, item_title, item_network = item[0], item[1], item[2]
                        if item_network in networks and item_id not in [sublist[0] for sublist in tv_shows]:
                            tv_shows.append([year, item_id, item_title, item_network])
    finally:
        print "saving tv_shows, years_already_processed, mashape_calls"
        saveobject(tv_shows, "program_data_files/tv_shows_basic")
        saveobject(years_already_processed, "program_data_files/years_already_processed")
        saveobject(mashape_calls, "mashape_calls")
    return tv_shows


def get_overview_text(tv_shows):
    try:
        tv_shows_overview = readobject("program_data_files/tv_shows_overview")
    except IOError:
        print "file: tv_shows_overview not found on disk. Starting new."
        tv_shows_overview = {}

    try:
        for show in tv_shows:
            show_id = show[1]
            if show_id not in tv_shows_overview.keys():
                print "Getting overview for  {0}".format(show_id)
                address = "".join(["http://thetvdb.com/api/5CCC7BF5A4FB7B8D/series/", show_id, "/all/en.zip"])
                # also need to close zipfile?
                with closing(urlopen(address)) as url:
                    zipfile = ZipFile(StringIO(url.read()))
                summary = zipfile.open("en.xml").read()
                tv_shows_overview[show_id] = xml_to_text(summary, node_name='Overview')
    finally:
        saveobject(tv_shows_overview, "program_data_files/tv_shows_overview")

    return tv_shows_overview


def get_keywords(overview):

    keywords = {}
    try:
        keywords = readobject("program_data_files/tv_shows_keywords")
    except IOError:
        print "file: tv_shows_keywords not found on disk. Starting new."

    alchemy_calls = {}
    try:
        alchemy_calls = readobject("alchemy_calls")
    except IOError:
        print "file alchemy_calls not found on disk"
    date_key = get_datecode()
    if date_key not in alchemy_calls:
        alchemy_calls[date_key] = 0
    max_per_day = 1000

    try:
        for show_id in overview.keys():
            if show_id not in keywords.keys() and alchemy_calls[date_key] < max_per_day:
                print "processing show id: {0}, call #: {1}".format(show_id, alchemy_calls[date_key])
                alchemy_calls[date_key] += 1
                keywords[show_id] = alchemy_keywords(overview[show_id].encode("utf-8"))
    finally:
        print "saving tv_shows_keywords, alchemy_calls"
        saveobject(keywords, "program_data_files/tv_shows_keywords")
        saveobject(alchemy_calls, "alchemy_calls")

    return keywords


def create_tv_corpus():
    # crawl site to generate list of tv shows. Site prefers you to use API so go gently
    year_range = range(1940, 2013)
    networks = ["CBS", "CNBC", "NBC", "CBC", "Bravo", "ABC", "HBO", "Cartoon Network",
                "A&E", "FOX", "TBS Superstation", "PBS", "Showtime", "Nickelodeon"]
    tv_shows = get_tv_shows(year_range, networks)

    # use api to get tv show summaries
    tv_shows_overview = get_overview_text(tv_shows)

    # use alchemy to get keywords from overview
    tv_shows_keywords = get_keywords(tv_shows_overview)

    # return tv_shows[[Show, Date(Year), Summary Text], [show 2], ...]


def main():
    create_tv_corpus()

if __name__ == "__main__":
    main()
