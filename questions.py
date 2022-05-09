# -*- coding: utf-8 -*-

import os
import random
import re
from collections import namedtuple
from logging import getLogger
import pandas as pd
import streamlit as st
logger = getLogger(__name__)


# state variable names
KEY_ANSWER_HISTORY = "answerHistory"

# style sheet
CSS = """
td.color {
    width: 80px;
    height: 80px;
    border: 5px white solid;
}

td.number {
    border: 1px white solid;
    text-align: center;
    vertical-align: bottom;
}
"""

@st.cache
def jis_data():
    logger.info("Loading JIS data")
    return pd.read_csv(os.path.join(os.path.dirname(__file__), "jis.csv"), encoding="utf8")

@st.cache
def pccs_data():
    logger.info("Loading PCCS data")
    return pd.read_csv(os.path.join(os.path.dirname(__file__), "pccs.csv"), encoding="utf8")


Color = namedtuple("Color", "name reading rgb info")

class Question:
    def show_question(self):
        st.write("This is a dummy question")
    
    def show_result(self, answer):
        st.write("Your answer is {}".format(answer))


class JIStoColor(Question):
    def __init__(self, n=4, distinct_rgb=True, distinct_info=True, same_category=True, distance_threshold=-1):
        self.colors = choose_jis_colors(n=n, distinct_rgb=distinct_rgb, distinct_info=distinct_info, same_category=same_category, distance_threshold=distance_threshold)
        self.answer_index = random.randint(0, n-1)
        self.user_answer = None
        logger.info("Colors: %s, answer: %s", self.colors, self.answer_index)

    @property
    def _choices(self):
        return list(range(1, len(self.colors) + 1))

    @property
    def _choices_details(self):
        # radio items to show with answers
        return ["{}. {} ({}, {}, {})".format(c, col.name, col.reading, col.info, col.rgb) for c,col in zip(self._choices, self.colors)]

    @property
    def _question_markdown(self):
        c = self.colors[self.answer_index]
        answer = "{} ({})".format(c.name, c.reading)
        row1 = " ".join("""<td class="number">{}</td>""".format(c) for c in self._choices)
        row2 = " ".join("""<td class="color" bgcolor="{}"></td>""".format(c.rgb) for c in self.colors)
        markdown = """
        **{}** はどれ？
        <table><tr>{}</tr><tr> {}</tr></table>
        """.format(answer, row1, row2)
        return markdown

    @property
    def _details_markdown(self):
        # additional info to show with the result
        return None
  
    @property
    def _user_answer_index(self):
        # maps index corresponding to the user's answer
        return self._choices.index(self.user_answer)

    def show_question(self):
        markdown = self._question_markdown
        st.markdown(markdown, unsafe_allow_html=True)        
        r = st.radio("", self._choices)
        if st.button("ENTER"):
            self.user_answer = r
            logger.info("User answer is given: %s", self.user_answer)
            _update_history(self._user_answer_index == self.answer_index)
            st.experimental_rerun()

    def show_result(self):
        logger.info("User answer: %s", self.user_answer)
        markdown = self._question_markdown
        st.markdown(markdown, unsafe_allow_html=True)
        st.radio("", self._choices_details, disabled=True, index=self._user_answer_index)

        message = "**Goog job!**" if (self._user_answer_index == self.answer_index) else "Not correct..."
        message += "　Answer: **{}**".format(self._choices[self.answer_index])
        st.markdown(message)

        details = self._details_markdown
        if details is not None:
            st.markdown(details, unsafe_allow_html=True)


class JIStoInfo(JIStoColor):
    @property
    def _choices(self):
        return [c.info for c in self.colors]

    @property
    def _choices_details(self):
        # radio items to show with answers
        return self._choices

    @property
    def _question_markdown(self):
        c = self.colors[self.answer_index]
        answer = "{} ({})".format(c.name, c.reading)
        markdown = """
        **{}** はどんな色？
        """.format(answer)
        return markdown

    @property
    def _details_markdown(self):
        # additional info to show with the result
        rgb = self.colors[self.answer_index].rgb
        return """<table><tr><td class="color" bgcolor="{}"></td></tr></table>""".format(rgb)


class ColorToJIS(JIStoColor):
    @property
    def _question_markdown(self):
        rgb = self.colors[self.answer_index].rgb
        markdown = """
        これは何色？
        <table><tr><td class="color" bgcolor="{}"></td></tr></table>
        """.format(rgb)
        return markdown

    @property
    def _choices(self):
        return ["{} ({})".format(col.name, col.reading) for col in self.colors]

    @property
    def _choices_details(self):
        # radio items to show with answers
        return ["{} ({}, {}, {})".format(col.name, col.reading, col.info, col.rgb) for col in self.colors]


class PCCStoColor(Question):
    def __init__(self, n=4, distance_threshold=-1):
        self.colors = choose_pccs_colors(n=n, distance_threshold=distance_threshold)
        self.answer_index = random.randint(0, n-1)
        self.user_answer = None
        logger.info("Colors: %s, answer: %s", self.colors, self.answer_index)

    @property
    def _choices(self):
        return list(range(1, len(self.colors) + 1))

    @property
    def _choices_details(self):
        # radio items to show with answers
        return ["{}. {} ({})".format(c, col.name, col.rgb) for c,col in zip(self._choices, self.colors)]

    @property
    def _question_markdown(self):
        c = self.colors[self.answer_index]
        answer = c.name
        row1 = " ".join("""<td class="number">{}</td>""".format(c) for c in self._choices)
        row2 = " ".join("""<td class="color" bgcolor="{}"></td>""".format(c.rgb) for c in self.colors)
        markdown = """
        **{}** はどれ？
        <table><tr>{}</tr><tr> {}</tr></table>
        """.format(answer, row1, row2)
        return markdown

    @property
    def _details_markdown(self):
        # additional info to show with the result
        return None
  
    @property
    def _user_answer_index(self):
        # maps index corresponding to the user's answer
        return self._choices.index(self.user_answer)

    def show_question(self):
        markdown = self._question_markdown
        st.markdown(markdown, unsafe_allow_html=True)        
        r = st.radio("", self._choices)
        if st.button("ENTER"):
            self.user_answer = r
            logger.info("User answer is given: %s", self.user_answer)
            _update_history(self._user_answer_index == self.answer_index)
            st.experimental_rerun()

    def show_result(self):
        logger.info("User answer: %s", self.user_answer)
        markdown = self._question_markdown
        st.markdown(markdown, unsafe_allow_html=True)
        st.radio("", self._choices_details, disabled=True, index=self._user_answer_index)

        message = "**Goog job!**" if (self._user_answer_index == self.answer_index) else "Not correct..."
        message += "　Answer: **{}**".format(self._choices[self.answer_index])
        st.markdown(message)

        details = self._details_markdown
        if details is not None:
            st.markdown(details, unsafe_allow_html=True)


class ColorToPCCS(PCCStoColor):
    @property
    def _choices(self):
        return [c.name for c in self.colors]

    @property
    def _choices_details(self):
        # radio items to show with answers
        return ["{} ({})".format(col.name, col.rgb) for col in self.colors]

    @property
    def _question_markdown(self):
        rgb = self.colors[self.answer_index].rgb
        markdown = """
        この色のPCCS表記は？
        <table><tr><td class="color" bgcolor="{}"></td></tr></table>
        """.format(rgb)
        return markdown

    @property
    def _details_markdown(self):
        # additional info to show with the result
        return None


def _rgb_distance(x, y):
    # x, y are string of format "#RRGGBB"
    def _to_tuple(x):
        x = re.sub(r"[^0-9a-fA-F]", "", x)
        assert len(x) == 6, "invalid rgb string '%x'".format(x)
        out = tuple(int(x[i:(i+2)], 16) for i in range(0, 6, 2))
        return out
    a = _to_tuple(x)
    b = _to_tuple(y)
    logger.info("%s --> %s, %s --> %s", x, a, y, b)
    dist = sum((i-j)**2 for i,j in zip(a,b))**0.5
    logger.info("Distance between '%s' (%s) and '%s' (%s) is %s", x, a, y, b, dist)
    return dist


def _update_history(result): 
    if KEY_ANSWER_HISTORY not in st.session_state:
        st.session_state[KEY_ANSWER_HISTORY] = [result]
    else:
        st.session_state[KEY_ANSWER_HISTORY].append(result)


def choose_jis_colors(n=4, distinct_rgb=True, distinct_info=True, same_category=True, distance_threshold=-1):
    # pick n jis colors
    x = jis_data().copy()
    # shuffle beforehand remove duplicates in a random manner
    x = x.sample(frac=1).reset_index(drop=True)
    
    if distinct_rgb and len(x) > n:
        # remove exactly the same RGB
        s1 = len(x)
        x = x.drop_duplicates(subset="rgb", keep="first").reset_index(drop=True)
        logger.info("Distinct RGB filtering %d --> %d", s1, len(x))
    if distinct_info and len(x) > n:
        # remove exactly the same info
        s1 = len(x)
        x = x.drop_duplicates(subset="feature_word", keep="first").reset_index(drop=True)
        logger.info("Distinct info filtering %d --> %d", s1, len(x))
    if same_category and len(x) > n:
        # choose a color group to ensure some similarity
        # currently, we group by color category
        # we may want to add more variation
        group = random.choice(x.category_color_en)
        logger.info("Group: '%s'", group)
        s1 = len(x)
        x = x[x.category_color_en == group]
        logger.info("Same category filtering %d --> %d", s1, len(x))
    if distance_threshold > 0 and len(x) > n:
        # pick a random benchmark color and filter only colors within distance threshold
        bench = random.choice(x.rgb)
        logger.info("Benchmark color: '%s'", bench)
        distances = [_rgb_distance(bench, r) for r in x.rgb]
        # adjust threshold to keep n records
        dist_n = sorted(distances)[n+5]
        threshold = max(distance_threshold, dist_n)
        if threshold != distance_threshold:
            logger.info("Threshold adjusted %s --> %s to make sure sufficient records (%d)", distance_threshold, threshold, n)
        s1 = len(x)
        x = x[[d <= threshold for d in distances]]
        logger.info("Distance threshold filtering %d --> %d", s1, len(x))

    tmp = x.sample(n)
    colors = [Color(row.colorname, row.reading, row.rgb, row.feature_word) for _, row in tmp.iterrows()]
    return colors


def choose_pccs_colors(n=4, distance_threshold=-1):
    # pick n pccs colors
    x = pccs_data().copy()
    # shuffle beforehand remove duplicates in a random manner
    x = x.sample(frac=1).reset_index(drop=True)

    if distance_threshold > 0 and len(x) > n:
        # pick a random benchmark color and filter only colors within distance threshold
        bench = random.choice(x.rgb)
        logger.info("Benchmark color: '%s'", bench)
        distances = [_rgb_distance(bench, r) for r in x.rgb]
        # adjust threshold to keep sufficient records
        dist_n = sorted(distances)[n+5]
        threshold = max(distance_threshold, dist_n)
        if threshold != distance_threshold:
            logger.info("Threshold adjusted %s --> %s to make sure sufficient records (%d)", distance_threshold, threshold, n)
        s1 = len(x)
        x = x[[d <= threshold for d in distances]]
        logger.info("Distance threshold filtering %d --> %d", s1, len(x))

    tmp = x.sample(n)
    colors = [Color(row.pccs, "", row.rgb, row.pccs_attr) for _, row in tmp.iterrows()]
    return colors

def generate_question(question_type):
    if question_type == "jis_to_color":
        r = random.random()
        if r <= 0.333:
            same_category = False
            distance_threshold = -1
        elif r <= 0.667:
            same_category = True
            distance_threshold = -1
        else:
            same_category = False
            distance_threshold = 50
        return JIStoColor(same_category=same_category, distance_threshold=distance_threshold)

    elif question_type == "color_to_jis":
        r = random.random()
        if r <= 0.333:
            same_category = False
            distance_threshold = -1
        elif r <= 0.667:
            same_category = True
            distance_threshold = -1
        else:
            same_category = False
            distance_threshold = 50
        return ColorToJIS(same_category=same_category, distance_threshold=distance_threshold)

    elif question_type == "jis_to_info":
        r = random.random()
        if r <= 0.333:
            same_category = False
            distance_threshold = -1
        elif r <= 0.667:
            same_category = True
            distance_threshold = -1
        else:
            same_category = False
            distance_threshold = 50
        return JIStoInfo(same_category=same_category, distance_threshold=distance_threshold)

    elif question_type == "pccs_to_color":
        r = random.random()
        if r <= 0.333:
            distance_threshold = -1
        elif r <= 0.667:
            distance_threshold = 100
        else:
            distance_threshold = 50
        return PCCStoColor(distance_threshold=distance_threshold)

    elif question_type == "color_to_pccs":
        r = random.random()
        if r <= 0.333:
            distance_threshold = -1
        elif r <= 0.667:
            distance_threshold = 100
        else:
            distance_threshold = 50
        return ColorToPCCS(distance_threshold=distance_threshold)

    return ValueError("Question type not supported: '{}'".format(question_type))