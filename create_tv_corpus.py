"""
Create corpus of tv shows from thetvdb.com
"""

__author__ = 'Aaron'

from urllib import quote_plus, urlopen
from projectutils import xml_to_text, readobject, saveobject
import unirest
import re
from StringIO import StringIO
from zipfile import ZipFile
from contextlib import closing


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
    try:
        tv_shows = readobject("program_data_files/tv_shows_basic")
    except IOError:
        tv_shows = []
        print "file: tv_shows_basic not found"

    try:
        years_already_processed = readobject("program_data_files/years_already_processed")
    except IOError:
        years_already_processed = []
        print "file: years_already_processed not found"

    mashape_key = readobject("mashape_key")

    for year in year_range:
        try:
            if year not in years_already_processed:
                print "processing {0}".format(year)
                search_url = construct_search_url(year)
                mashape_query = construct_mashape_query(search_url)
                mashape_header = {"X-Mashape-Authorization": mashape_key}
                try:
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
            saveobject(tv_shows, "tv_shows_basic")
            saveobject(years_already_processed, "years_already_processed")
    return tv_shows


def get_overview_text(tv_shows):
    # TODO save show overviews as dictionary. Look up and append to tv shows
    # FIXME this does not work right now. I overwrite any additions with the disk version of tv_shows
    try:
        tv_shows = readobject("program_data_files/tv_shows_overview")
    except IOError:
        print "file: tv_shows_overview not found on disk"

    try:
        for show in tv_shows:
            if len(show) == 4:
                show_id = show[1]
                print show_id
                address = "".join(["http://thetvdb.com/api/5CCC7BF5A4FB7B8D/series/", show_id, "/all/en.zip"])
                # also need to close zipfile?
                with closing(urlopen(address)) as url:
                    zipfile = ZipFile(StringIO(url.read()))
                summary = zipfile.open("en.xml").read()
                show.append(xml_to_text(summary, node_name='Overview'))
    finally:
        saveobject(tv_shows, "tv_shows_overview")

    return tv_shows


def create_tv_corpus():
    # crawl site to generate list of tv shows. Site prefers you to use API so go gently
    year_range = range(1940, 1985)
    networks = ["CBS", "CNBC", "NBC", "CBC", "Bravo", "ABC", "HBO", "Cartoon Network",
                "A&E", "FOX", "TBS Superstation", "PBS", "Showtime", "Nickelodeon"]
    tv_shows = get_tv_shows(year_range, networks)

    # use api to get tv show summaries
    tv_shows = get_overview_text(tv_shows)

    # return tv_shows[[Show, Date(Year), Summary Text], [show 2], ...]


def main():
    create_tv_corpus()

if __name__ == "__main__":
    main()
