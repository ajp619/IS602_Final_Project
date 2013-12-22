"""
IS602 Final Project

Do the themes we see as a child show up later in political speeches
"""
__author__ = 'Aaron'

import create_speech_corpus
import create_tv_corpus
from projectutils import create_heat_map, plot_heat_map


def get_speech_seed():
    return ["http://www.americanrhetoric.com/speechbanka-f.htm",
            "http://www.americanrhetoric.com/speechbankg-l.htm",
            "http://www.americanrhetoric.com/speechbankm-r.htm]",
            "http://www.americanrhetoric.com/speechbanks-z.htm"]


def main():
    # Get seed links for speech crawl
    speech_seeds = get_speech_seed()

    # Get summary of speech corpus
    speech_summary = create_speech_corpus.get_corpus(speech_seeds)

    # Get summary of tv corpus
    tv_summary = create_tv_corpus.create_tv_corpus()

    # print "speech length = {0}, tv length = {1}".format(len(speech_summary), len(tv_summary))

    #Heat Map:
    heat_map = create_heat_map(source=tv_summary,
                               response=speech_summary,
                               max_keywords=50,
                               start_year=1960,
                               interval=30)

    plot_heat_map(heat_map)


if __name__ == "__main__":
    main()
