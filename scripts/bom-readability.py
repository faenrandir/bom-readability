#!/usr/bin/env python3

import argparse
import json
import re
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy
import seaborn as sns
import textstat
from matplotlib import pyplot as plt
from matplotlib.offsetbox import AnnotationBbox
from matplotlib.offsetbox import TextArea

from bom_readability.bible_verses_in_bom import BIBLE_VERSES_IN_BOM

# I think difficult_words is a summation of difficult words and so is
# length dependent?  Dropping difficult_words.  If shown to be length
# independent will add back in.
METRICS = {
    # "difficult_words",

    # textstat key: (title, x axis, location at top for text)
    "smog_index": ("SMOG", "grade level to comprehend", "left"),
    "coleman_liau_index": ("Coleman–Liau",  "grade level to comprehend", "left"),
    "flesch_kincaid_grade": ("Flesch–Kincaid",  "grade level to comprehend", "right"),
    "automated_readability_index": ("Automated Readability Index", "grade level to comprehend", "right"),
    "linsear_write_formula": ("Linsear Write", "grade level to comprehend", "right"),
    "gunning_fog": ("Gunning fog", "grade level to comprehend on first reading", "right"),
    "text_standard": ("python textstat consensus", "grade level to comprehend", "right"),
    "flesch_reading_ease": ("Flesch Reading Ease", "score", "left"),
    "dale_chall_readability_score": ("Dale–Chall", "score", "right"),
}

HORIZONTAL_ALIGN = dict(
    right=(0.95, 0.95),
    left=(0.05, 0.95),
)

BOXSTYLE = dict(
    right='larrow',
    left='rarrow',
)

def write_to_file(filename, text):
    with open(filename, 'w') as out:
        out.write(text)


parser = argparse.ArgumentParser()
parser.add_argument("bom_json_filename", help="bomdb exported json file of a BoM edition")
parser.add_argument("cowdery_letter", help="txt file of the Oct 1829 letter")
parser.add_argument("preface_to_bom", help="preface to the Book of Mormon")
args = parser.parse_args()

bom_json = json.loads(open(args.bom_json_filename).read())
letter_to_cowdery_oct_1829 = open(args.cowdery_letter).read()
preface_to_bom = open(args.preface_to_bom).read()


def convert_text_standard_to_numeric(grade_levels):
    return sum([int(num_str) for num_str in TEXT_STANDARD_RE.match(grade_levels).groups()]) / 2


def measure_readability(text):
    data = {metric: getattr(textstat, metric)(text) for metric in METRICS.keys()}
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

        write_to_file(f"{chapter}.txt", data['text'])
    else:
        print(f"CHAPTER {len(data['text'])} < {MIN_CHAR_LENGTH}; dropping", chapter)

letter_to_cowdery_readability = measure_readability(letter_to_cowdery_oct_1829)
preface_to_bom_readability = measure_readability(preface_to_bom)
book_of_mormon_less_bible_readability = measure_readability(all_book_of_mormon_text_without_bible)

write_to_file("1992-bom-all-less-bible.txt", all_book_of_mormon_text_without_bible)

# pyplot.rcdefaults()

def gte_precent(value, sorted_values):
    num_values_gte = 0
    for value in sorted_values:
        if letter_to_cowdery_readability[metric] >= value:
            num_values_gte += 1
        else:
            break
    return (num_values_gte / len(sorted_values)) * 100


sns.set()


for plot_num, (metric, values) in enumerate(readability_metrics.items(), 1):
    plt.subplot(3, 3, plot_num)

    sorted_values = sorted(values)
    cowdery_gte_chapters_percent = gte_precent(letter_to_cowdery_readability[metric], sorted_values)

    chapter_seq = numpy.arange(len(values))

    # scatter = this_plot.scatter(chapter_seq, values, alpha=0.9, label='Book of Mormon Chapters')
    distplot = sns.distplot(values, bins=32, kde=True, rug=False)
    # distplot = sns.distplot(values, kde=True, rug=False)
    letter_line = plt.axvline(x=letter_to_cowdery_readability[metric], color='red', alpha=0.5, linestyle=":", linewidth=2)
    preface_line = plt.axvline(x=preface_to_bom_readability[metric], color='orange', alpha=0.6, linestyle=":", linewidth=2)
    bom_line = plt.axvline(x=book_of_mormon_less_bible_readability[metric], color='black', alpha=0.5, linestyle="--", linewidth=3)

    axes = plt.gca()

    text_halign = METRICS[metric][2]
    horizontal_alignment = HORIZONTAL_ALIGN[text_halign]
    boxstyle = BOXSTYLE[text_halign]
    axes.text(
        *horizontal_alignment,
        f"Letter ≥ {cowdery_gte_chapters_percent:.0f}% chapters",
        ha=text_halign,
        va='top',
        color='black',
        backgroundcolor='w',
        transform=axes.transAxes,
        # bbox=dict(facecolor='none', color='white', edgecolor='black',  alpha=None, boxstyle='round,pad=0.5')
        bbox=dict(facecolor='none', color='white', edgecolor='black',  alpha=None, boxstyle=boxstyle)
        # t.set_bbox(dict(facecolor='red', alpha=0.5, edgecolor='red'))
    )

    axes.set_xlabel(METRICS[metric][1])
    distplot_rect = distplot.get_children()[0]
    if plot_num == 3:
        plt.legend(
            [distplot_rect, letter_line, bom_line],
            ['Book of Mormon chapters (frequency)', '1829 Letter to Cowdery', 'Book of Mormon'],
            prop={'size': 20},
            bbox_to_anchor=(0.7, 1.45),
        )


    axes.set_title(METRICS[metric][0])
    # .title(metric.replace("_", " "), fontsize=24)


# figure.text(0.5, 0.04, 'chapter', ha='center', va='center')
# figure.text(0.06, 0.5, 'score', ha='center', va='center', rotation='vertical')
# figure.suptitle('Book of Mormon readability')

# all_labels = [axes.get_legend_handles_labels() for axes in figure.axes]
# features, labels = [sum(lol, []) for lol in zip(*all_labels)]
# figure.legend(features, labels)


plt.show()


print(" | ".join(['metric', 'BoM', '1829 Letter']))
print("---: | :--- | :---")

for metric in letter_to_cowdery_readability.keys():
    vals = [
        metric,
        "{:.1f}".format(book_of_mormon_less_bible_readability[metric]),
        "{:.1f}".format(letter_to_cowdery_readability[metric]),
    ]
    print(" | ".join(vals))
