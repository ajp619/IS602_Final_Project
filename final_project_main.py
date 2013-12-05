"""
IS602 Final Project

Do the themes we see as a child show up later in political speeches
"""


import create_speech_corpus


def get_speech_seed():
    return ["http://www.americanrhetoric.com/speechbanka-f.htm",
            "http://www.americanrhetoric.com/speechbankg-l.htm",
            "http://www.americanrhetoric.com/speechbankm-r.htm]",
            "http://www.americanrhetoric.com/speechbanks-z.htm"]


def main():
    # Get seed links for speech crawl
    speech_seed = get_speech_seed()

    # Create speech corpus
    speech_corpus = create_speech_corpus.get_corpus(speech_seed)


if __name__ == "__main__":
    main()

__author__ = 'Aaron'
