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


def get_tv_shows(year_range, networks, ignore_ids):

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

    need_save_mashape = False
    need_save_shows = False

    mashape_key = readobject("mashape_key")

    try:
        for year in year_range:
            if year not in years_already_processed and mashape_calls[date_key] < max_per_day:
                print "processing {0}".format(year)
                search_url = construct_search_url(year)
                mashape_query = construct_mashape_query(search_url)
                mashape_header = {"X-Mashape-Authorization": mashape_key}
                try:
                    need_save_mashape = True
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
                        if (item_network in networks and
                                    item_id not in [sublist[0] for sublist in tv_shows] and
                                    item_id not in ignore_ids):
                            need_save_shows = True
                            tv_shows.append([year, item_id, item_title, item_network])
    finally:
        if need_save_mashape:
            print "saving mashape_calls, years_already_processed"
            saveobject(years_already_processed, "program_data_files/years_already_processed")
            saveobject(mashape_calls, "mashape_calls")
        else:
            print "no changes to mashape_calls or years_already_processed"

        if need_save_shows:
            print "saving tv_shows"
            saveobject(tv_shows, "program_data_files/tv_shows_basic")
        else:
            print "no changes to tv_shows_basic"
    return tv_shows


def get_overview_text(tv_shows):
    try:
        tv_shows_overview = readobject("program_data_files/tv_shows_overview")
    except IOError:
        print "file: tv_shows_overview not found on disk. Starting new."
        tv_shows_overview = {}

    need_save_overview = False

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
                need_save_overview = True
                tv_shows_overview[show_id] = xml_to_text(summary, node_name='Overview')
    finally:
        if need_save_overview:
            print "saving tv_shows_overview"
            saveobject(tv_shows_overview, "program_data_files/tv_shows_overview")
        else:
            print "no changes to tv_shows_overview"

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
    need_save_keywords = False

    try:
        for show_id in overview.keys():
            if show_id not in keywords.keys() and alchemy_calls[date_key] < max_per_day:
                print "processing show id: {0}, call #: {1}".format(show_id, alchemy_calls[date_key])
                alchemy_calls[date_key] += 1
                need_save_keywords = True
                keywords[show_id] = alchemy_keywords(overview[show_id].encode("utf-8"))
    finally:
        if need_save_keywords:
            print "saving tv_shows_keywords, alchemy_calls"
            saveobject(keywords, "program_data_files/tv_shows_keywords")
            saveobject(alchemy_calls, "alchemy_calls")
        else:
            print "no changes to tv_shows_keywords, alchemy_calls"
        return keywords


def summarize(tv_shows, keywords):
    summary = dict()
    missing_keywords_flag = False
    for show in tv_shows:
        try:
            year = int(show[0])
            tvid = show[1]
            title = show[2]
            network = show[3]
            words = keywords[tvid]

            summary[tvid] = dict(year=year, title=title, network=network, keywords=words)

        except KeyError:
            # print "No keywords. Skipping show {0} ({1}))".format(title, tvid) # Uncomment to debug
            missing_keywords_flag = True
    if missing_keywords_flag:
        print "There were missing keywords"
    return summary


def create_tv_corpus():
    # crawl site to generate list of tv shows. Site prefers you to use API so go gently
    year_range = range(1940, 2013)

    # These are the networks to process. Ignore things from, for instance, the BBC
    networks = ["CBS", "CNBC", "NBC", "CBC", "Bravo", "ABC", "HBO", "Cartoon Network",
                "A&E", "FOX", "TBS Superstation", "PBS", "Showtime", "Nickelodeon"]

    # There are a few shows that cause errors when processing. Ignore these.
    ignore_ids = ['70330']

    tv_shows = get_tv_shows(year_range, networks, ignore_ids)

    # use api to get tv show summaries
    tv_shows_overview = get_overview_text(tv_shows)

    # use alchemy to get keywords from overview
    tv_shows_keywords = get_keywords(tv_shows_overview)

    # Create a summary dictionary
    summary = summarize(tv_shows, tv_shows_keywords)

    # return summary = dict{tvid:{year=year, title=title, network=network, keywords={word=value}}}
    return summary


def main():
    summary = create_tv_corpus()
    total_errors = 0
    for key in summary.keys():
        try:
            len(summary[key]['keywords'])
        except KeyError:
            total_errors += 1
    print "Total Key Errors in summary file = {0}".format(total_errors)


if __name__ == "__main__":
    main()
