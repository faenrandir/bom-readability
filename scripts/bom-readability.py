#!/usr/bin/env python3

import argparse
import json
import re
from collections import defaultdict

import matplotlib.pyplot as pyplot
import numpy
import seaborn
import textstat

from bom_readability.bible_verses_in_bom import BIBLE_VERSES_IN_BOM

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

parser = argparse.ArgumentParser()
parser.add_argument("bom_json_filename", help="bomdb exported json file of a BoM edition")
parser.add_argument("cowdery_letter", help="txt file of the Oct 1829 letter")
args = parser.parse_args()

bom_json = json.loads(open(args.bom_json_filename).read())
letter_to_cowdery_oct_1829 = open(args.cowdery_letter).read()


def convert_text_standard_to_numeric(grade_levels):
    return sum([int(num_str) for num_str in TEXT_STANDARD_RE.match(grade_levels).groups()]) / 2


def measure_readability(text):
    data = {metric: getattr(textstat, metric)(text) for metric in METRICS}
    data['text_standard'] = convert_text_standard_to_numeric(data['text_standard'])
    return data


BIBLE_VERSES_TO_EXCLUDE_EXPANDED = set()
for verse_indicator in BIBLE_VERSES_IN_BOM:
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

letter_to_cowdery_readability = measure_readability(letter_to_cowdery_oct_1829)
book_of_mormon_less_bible_readability = measure_readability(all_book_of_mormon_text_without_bible)

from matplotlib import pyplot
# pyplot.rcdefaults()

seaborn.set()

figure, axes = pyplot.subplots(3, 3)

for plot_num, (metric, values) in enumerate(readability_metrics.items()):
    axes_coordinates = divmod(plot_num, 3)
    this_plot = axes[axes_coordinates[0], axes_coordinates[1]]
    this_plot.set_xlim([-5, len(values) + 5])

    #this_plot.xlim(left=0)
    #this_plot.xlim(right=len(values))

    chapter_seq = numpy.arange(len(values))

    scatter = this_plot.scatter(chapter_seq, values, alpha=0.9, label='Book of Mormon Chapters')
    letter_line = this_plot.axhline(y=letter_to_cowdery_readability[metric], color='red', alpha=0.5, linestyle=":", linewidth=2, label='Oct 1829 Letter to Cowdery')
    bom_line = this_plot.axhline(y=book_of_mormon_less_bible_readability[metric], color='black', alpha=0.5, linestyle="--", linewidth=3, label='Complete Book of Mormon')
    if axes_coordinates == (0, 2):
        this_plot.legend(
            [scatter, letter_line, bom_line],
            ['Book of Mormon (chapters)', '1829 Letter to Cowdery', 'Book of Mormon'],
            prop={'size': 20},
            bbox_to_anchor=(1.03, 1.45),
        )

    this_plot.set_title(metric.replace("_", " "), fontsize=24)


# figure.text(0.5, 0.04, 'chapter', ha='center', va='center')
# figure.text(0.06, 0.5, 'score', ha='center', va='center', rotation='vertical')
# figure.suptitle('Book of Mormon readability')

# all_labels = [axes.get_legend_handles_labels() for axes in figure.axes]
# features, labels = [sum(lol, []) for lol in zip(*all_labels)]
# figure.legend(features, labels)


pyplot.show()


print(" | ".join(['metric', 'BoM', '1829 Letter']))
print("---: | :--- | :---")

for metric in letter_to_cowdery_readability.keys():
    vals = [
        metric,
        "{:.1f}".format(book_of_mormon_less_bible_readability[metric]),
        "{:.1f}".format(letter_to_cowdery_readability[metric]),
    ]
    print(" | ".join(vals))
