#!/usr/bin/env python3

import argparse
import json
import re
from collections import defaultdict

import textstat

LETTER_TO_COWDERY_OCT_1829 = """
I would inform you that I arrived at home on Sunday morning the fourth. After having a prosperous journey, and found all well, the people are all friendly to us except a few who are in opposition to everything, unless it is something that is axactly like themselves, and two of our most formidable persecutors are now under censure and are cited to a trial in the Church for crimes which, if true, are worse than all the Gold Book business.  We do not rejoice in the affliction of our enemies but we shall be glad to have truth prevail.
There begins to be a great call for our books in this country; the minds of the people are very much excited when they find that there is a copyright obtained and that there really are books about to be printed.
I have bought a horse from Mister Stowell and want someone to come after it as soon as is convenient.
Mister Stowell has a prospect of getting five or six hundred dollars, but he does not know for certain that he can get it, but he is a going to try, and if he can get the money he wants to pay it in immediately for books.
We want to hear from you and know how you prosper in the good work.
Give our best respects to Father and Mother and all our brothers and sisters. To Mister Harris and all the company concerned tell them that our prayers are put up daily for them that they may be prospered in every good word and work and that they may be preserved from sin here and from the consequence of sin hereafter.
And now dear brother, be faithful in the discharge of every duty looking for the reward of the righteous.
And now, may God of his infinite mercy keep and preserve us spotless until his coming and receive us all to rest with him in eternal repose through the attonement of Christ our Lord, Amen.
""".lstrip()


parser = argparse.ArgumentParser()
parser.add_argument("bom_json_filename", help="bomdb exported json file of a BoM edition")
args = parser.parse_args()

bom_json = json.loads(open(args.bom_json_filename).read())


# I think difficult_words is a summation of difficult words and so is
# length dependent?  Dropping difficult_words.  If shown to be length
# independent will add back in.
METRICS = [
    "flesch_reading_ease",
    "smog_index",
    "flesch_kincaid_grade",
    "coleman_liau_index",
    "automated_readability_index",
    "dale_chall_readability_score",
    # "difficult_words",
    "linsear_write_formula",
    "gunning_fog",
    "text_standard",
]

BIBLE_VERSES_TO_EXCLUDE = [
    "1 Nephi 20:*",
    "1 Nephi 21:*",
    "2 Nephi 6:6",
    "2 Nephi 6:7",
    "2 Nephi 6:16",
    "2 Nephi 6:17",
    "2 Nephi 6:18",
    "2 Nephi 7:*",
    "2 Nephi 8:*",
    "2 Nephi 9:50",
    "2 Nephi 9:51",
    "2 Nephi 10:9",
    "2 Nephi 12:*",
    "2 Nephi 13:*",
    "2 Nephi 14:*",
    "2 Nephi 15:*",
    "2 Nephi 16:*",
    "2 Nephi 17:*",
    "2 Nephi 18:*",
    "2 Nephi 19:*",
    "2 Nephi 20:*",
    "2 Nephi 21:*",
    "2 Nephi 22:*",
    "2 Nephi 23:*",
    "2 Nephi 24:*",
    "2 Nephi 27:25",
    "2 Nephi 27:26",
    "2 Nephi 27:27",
    "2 Nephi 27:28",
    "2 Nephi 27:29",
    "2 Nephi 27:30",
    "2 Nephi 27:31",
    "2 Nephi 27:32",
    "2 Nephi 27:33",
    "2 Nephi 27:34",
    "2 Nephi 30:9",
    "2 Nephi 30:11",
    "2 Nephi 30:12",
    "2 Nephi 30:13",
    "2 Nephi 30:14",
    "2 Nephi 30:15",
    "Mosiah 12:21",
    "Mosiah 12:22",
    "Mosiah 12:23",
    "Mosiah 12:24",
    "Mosiah 12:34",
    "Mosiah 12:35",
    "Mosiah 12:36",
    "Mosiah 13:12",
    "Mosiah 13:13",
    "Mosiah 13:14",
    "Mosiah 13:15",
    "Mosiah 13:16",
    "Mosiah 13:17",
    "Mosiah 13:18",
    "Mosiah 13:19",
    "Mosiah 13:20",
    "Mosiah 13:21",
    "Mosiah 13:22",
    "Mosiah 13:23",
    "Mosiah 13:24",
    "Mosiah 14:1",
    "Mosiah 14:2",
    "Mosiah 14:3",
    "Mosiah 14:4",
    "Mosiah 14:5",
    "Mosiah 14:6",
    "Mosiah 14:7",
    "Mosiah 14:8",
    "Mosiah 14:9",
    "Mosiah 14:10",
    "Mosiah 14:11",
    "Mosiah 14:12",
    "Mosiah 15:29",
    "Mosiah 15:30",
    "Mosiah 15:31",
    "Alma 42:2",
    "3 Nephi 12:3",
    "3 Nephi 12:4",
    "3 Nephi 12:5",
    "3 Nephi 12:6",
    "3 Nephi 12:7",
    "3 Nephi 12:8",
    "3 Nephi 12:9",
    "3 Nephi 12:10",
    "3 Nephi 12:11",
    "3 Nephi 12:12",
    "3 Nephi 12:13",
    "3 Nephi 12:14",
    "3 Nephi 12:15",
    "3 Nephi 12:16",
    "3 Nephi 12:17",
    "3 Nephi 12:18",
    "3 Nephi 12:19",
    "3 Nephi 12:20",
    "3 Nephi 12:21",
    "3 Nephi 12:22",
    "3 Nephi 12:23",
    "3 Nephi 12:24",
    "3 Nephi 12:25",
    "3 Nephi 12:26",
    "3 Nephi 12:27",
    "3 Nephi 12:28",
    "3 Nephi 12:29",
    "3 Nephi 12:30",
    "3 Nephi 12:31",
    "3 Nephi 12:32",
    "3 Nephi 12:33",
    "3 Nephi 12:34",
    "3 Nephi 12:35",
    "3 Nephi 12:36",
    "3 Nephi 12:37",
    "3 Nephi 12:38",
    "3 Nephi 12:39",
    "3 Nephi 12:40",
    "3 Nephi 12:41",
    "3 Nephi 12:42",
    "3 Nephi 12:43",
    "3 Nephi 12:44",
    "3 Nephi 12:45",
    "3 Nephi 12:48",
    "3 Nephi 13:1",
    "3 Nephi 13:2",
    "3 Nephi 13:3",
    "3 Nephi 13:4",
    "3 Nephi 13:5",
    "3 Nephi 13:6",
    "3 Nephi 13:7",
    "3 Nephi 13:8",
    "3 Nephi 13:9",
    "3 Nephi 13:10",
    "3 Nephi 13:11",
    "3 Nephi 13:12",
    "3 Nephi 13:13",
    "3 Nephi 13:14",
    "3 Nephi 13:15",
    "3 Nephi 13:16",
    "3 Nephi 13:17",
    "3 Nephi 13:18",
    "3 Nephi 13:19",
    "3 Nephi 13:20",
    "3 Nephi 13:21",
    "3 Nephi 13:22",
    "3 Nephi 13:23",
    "3 Nephi 13:24",
    "3 Nephi 13:25",
    "3 Nephi 13:26",
    "3 Nephi 13:27",
    "3 Nephi 13:28",
    "3 Nephi 13:29",
    "3 Nephi 13:30",
    "3 Nephi 13:31",
    "3 Nephi 13:32",
    "3 Nephi 13:33",
    "3 Nephi 13:34",
    "3 Nephi 14:1",
    "3 Nephi 14:2",
    "3 Nephi 14:3",
    "3 Nephi 14:4",
    "3 Nephi 14:5",
    "3 Nephi 14:6",
    "3 Nephi 14:7",
    "3 Nephi 14:8",
    "3 Nephi 14:9",
    "3 Nephi 14:10",
    "3 Nephi 14:11",
    "3 Nephi 14:12",
    "3 Nephi 14:13",
    "3 Nephi 14:14",
    "3 Nephi 14:15",
    "3 Nephi 14:16",
    "3 Nephi 14:17",
    "3 Nephi 14:18",
    "3 Nephi 14:19",
    "3 Nephi 14:20",
    "3 Nephi 14:21",
    "3 Nephi 14:22",
    "3 Nephi 14:23",
    "3 Nephi 14:24",
    "3 Nephi 14:25",
    "3 Nephi 14:26",
    "3 Nephi 14:27",
    "3 Nephi 16:18",
    "3 Nephi 16:19",
    "3 Nephi 16:20",
    "3 Nephi 20:16",
    "3 Nephi 20:17",
    "3 Nephi 20:18",
    "3 Nephi 20:19",
    "3 Nephi 20:23",
    "3 Nephi 20:24",
    "3 Nephi 20:25",
    "3 Nephi 20:26",
    "3 Nephi 21:12",
    "3 Nephi 21:13",
    "3 Nephi 21:14",
    "3 Nephi 21:15",
    "3 Nephi 21:16",
    "3 Nephi 21:17",
    "3 Nephi 21:18",
    "3 Nephi 22:1",
    "3 Nephi 22:2",
    "3 Nephi 22:3",
    "3 Nephi 22:4",
    "3 Nephi 22:5",
    "3 Nephi 22:6",
    "3 Nephi 22:7",
    "3 Nephi 22:8",
    "3 Nephi 22:9",
    "3 Nephi 22:10",
    "3 Nephi 22:11",
    "3 Nephi 22:12",
    "3 Nephi 22:13",
    "3 Nephi 22:14",
    "3 Nephi 22:15",
    "3 Nephi 22:16",
    "3 Nephi 22:17",
    "3 Nephi 24:1",
    "3 Nephi 24:2",
    "3 Nephi 24:3",
    "3 Nephi 24:4",
    "3 Nephi 24:5",
    "3 Nephi 24:6",
    "3 Nephi 24:7",
    "3 Nephi 24:8",
    "3 Nephi 24:9",
    "3 Nephi 24:10",
    "3 Nephi 24:11",
    "3 Nephi 24:12",
    "3 Nephi 24:13",
    "3 Nephi 24:14",
    "3 Nephi 24:15",
    "3 Nephi 24:16",
    "3 Nephi 24:17",
    "3 Nephi 24:18",
    "3 Nephi 25:1",
    "3 Nephi 25:2",
    "3 Nephi 25:3",
    "3 Nephi 25:4",
    "3 Nephi 25:5",
    "3 Nephi 25:6",
    "Mormon 9:22",
    "Mormon 9:23",
    "Mormon 9:24",
]


def convert_text_standard_to_numeric(grade_levels):
    return sum([int(num_str) for num_str in TEXT_STANDARD_RE.match(grade_levels).groups()]) / 2


def measure_readability(text):
    data = {metric: getattr(textstat, metric)(text) for metric in METRICS}
    data['text_standard'] = convert_text_standard_to_numeric(data['text_standard'])
    return data


BIBLE_VERSES_TO_EXCLUDE_EXPANDED = set()
for verse_indicator in BIBLE_VERSES_TO_EXCLUDE:
    if "*" in verse_indicator:
        for num in range(1, 101):
            BIBLE_VERSES_TO_EXCLUDE_EXPANDED.add(
                verse_indicator.replace("*", str(num))
            )
    else:
        BIBLE_VERSES_TO_EXCLUDE_EXPANDED.add(verse_indicator)


chapter_data = defaultdict(dict)
for book, chapters in bom_json['contents'].items():
    for chapter, verses in chapters.items():
        chapter_key = f"{book} {chapter}"
        chapter_data[chapter_key]['verses'] = []
        for verse, edition_text in verses.items():
            if verse in BIBLE_VERSES_TO_EXCLUDE_EXPANDED:
                continue
            for edition, text in edition_text.items():
                chapter_data[chapter_key]['verses'].append(text)


TEXT_STANDARD_RE = re.compile(r"([\-\d]+)[tsnr][htd] and ([\-\d]+)[tsnr][htd] grade")

for chapter, data in chapter_data.items():
    data['text'] = ''.join([verse + "\n" for verse in data['verses']])
    data['readability'] = measure_readability(data['text'])
    data['text_length'] = len(data['text'])

all_book_of_mormon_text_without_bible = ''.join([data['text'] for data in chapter_data.values()])

MIN_CHAR_LENGTH = 50

readability_metrics = defaultdict(list)
for chapter, data in chapter_data.items():
    if len(data['text']) >= MIN_CHAR_LENGTH:
        for metric, score in data['readability'].items():
            readability_metrics[metric].append(score)

letter_to_cowdery_readability = measure_readability(LETTER_TO_COWDERY_OCT_1829)
book_of_mormon_less_bible_readability = measure_readability(all_book_of_mormon_text_without_bible)

import matplotlib.pyplot as plt; plt.rcdefaults()
import numpy as np
import matplotlib.pyplot as plt
import seaborn

seaborn.set()

figure, axes = plt.subplots(3, 3)

# axes.ylabel('score')
# figure.ylabel('score')
# figure.legend()

for plot_num, (metric, values) in enumerate(readability_metrics.items()):
    axes_coordinates = divmod(plot_num, 3)
    this_plot = axes[axes_coordinates[0], axes_coordinates[1]]

    chapter_seq = np.arange(len(values))

    this_plot.scatter(chapter_seq, values, alpha=0.9, label='Book of Mormon Chapters')
    this_plot.axhline(y=letter_to_cowdery_readability[metric], color='red', alpha=0.5, linestyle=":", linewidth=2, label='Oct 1829 Letter to Cowdery')
    this_plot.axhline(y=book_of_mormon_less_bible_readability[metric], color='black', alpha=0.5, linestyle="--", linewidth=3, label='Complete Book of Mormon')
    this_plot.set_title(metric)


figure.text(0.5, 0.04, 'chapter', ha='center', va='center')
figure.text(0.06, 0.5, 'score', ha='center', va='center', rotation='vertical')
figure.suptitle('Book of Mormon readability')

    # print(readability_metrics)

# all_labels = [axes.get_legend_handles_labels() for axes in figure.axes]
# features, labels = [sum(lol, []) for lol in zip(*all_labels)]
# figure.legend(features, labels)


plt.show()

print(book_of_mormon_less_bible_readability)
# len(LETTER_TO_COWDERY_OCT_1829)

# print("BOOK", measure_readability(whole_book))


