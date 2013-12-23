"""
IS602 Final Project

Do the themes we see as a child show up later in political speeches
"""
__author__ = 'Aaron'

import create_speech_corpus
import create_tv_corpus
from projectutils import create_heat_map, plot_heat_map
import matplotlib.pyplot as plt

def get_speech_seed():
    """
    Links to list of speeches on americanrhetoric. Starting point for speech crawl.
    """
    return ["http://www.americanrhetoric.com/speechbanka-f.htm",
            "http://www.americanrhetoric.com/speechbankg-l.htm",
            "http://www.americanrhetoric.com/speechbankm-r.htm]",
            "http://www.americanrhetoric.com/speechbanks-z.htm"]


def visualization(tv_summary, speech_summary, start, stop, mode='interactive'):
    """
    Create final output

    Two modes, save and interactive.
        Use interactive to explore small batches of output
        Use save to output a large number of years to output/outputYEAR.png
    """

    # There was a problem with unicode to ascii errors cropping up again in matplotlib
    # TODO fix encoding errors for the following years
    skip_years = [1941, 1942, 1945, 1995, 2005, 2006, 2010, 2011]
    for start_year in [year for year in range(start, stop) if year not in skip_years]:
        print "Creating figure for " + str(start_year)
        heat_map, keywords = create_heat_map(source=tv_summary,
                                             response=speech_summary,
                                             max_keywords=45,
                                             start_year=start_year,
                                             interval=50)

        fig = plot_heat_map(heat_map, keywords, start_year)

        if mode == 'save':
            # Save fig to file
            fig.set_size_inches(11, 7.5)
            fig.savefig('output/output' + str(start_year) + '.png', dpi=100)
        else:
            plt.draw()
    if mode != 'save':
        plt.show()


def main():
    # Get seed links for speech crawl
    speech_seeds = get_speech_seed()

    # Get summary of speech corpus
    speech_summary = create_speech_corpus.get_corpus(speech_seeds)

    # Get summary of tv corpus
    tv_summary = create_tv_corpus.create_tv_corpus()

    #Visualization with Heat Map:
    #   Create output for years from start to stop
    #   should be able to set this to limits, but I will save
    #   this with a smaller range to begin
    start = 1970            # data starts at 1940
    stop = 1972             # data stops at 2013
    mode = 'interactive'    # mode = 'interactive' or 'save'
    visualization(tv_summary, speech_summary, start, stop, mode)


if __name__ == "__main__":
    main()
