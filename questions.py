# -*- coding: utf-8 -*-

import os
import random
from collections import namedtuple
from logging import getLogger
import pandas as pd
import streamlit as st
logger = getLogger(__name__)


# state variable names
KEY_ANSWER_HISTORY = "answerHistory"

@st.cache
def jis_data():
    logger.info("Loading JIS data")
    return pd.read_csv(os.path.join(os.path.dirname(__file__), "jis.csv"), encoding="utf8")


Color = namedtuple("Color", "name reading rgb info")

class Question:
    def show_question(self):
        st.write("This is a dummy question")
    
    def show_result(self, answer):
        st.write("Your answer is {}".format(answer))


class JIStoColor(Question):
    def __init__(self, n=4):
        self.colors = choose_jis_colors(n)
        self.answer_index = random.randint(0, n-1)
        self.user_answer = None
        logger.info("Colors: %s, answer: %s", self.colors, self.answer_index)

    @property
    def _choices(self):
        return list(range(1, len(self.colors) + 1))
        
    @property
    def _question_markdown(self):
        c = self.colors[self.answer_index]
        answer = "{} ({})".format(c.name, c.reading)
        n = len(self.colors)
        row1 = " ".join("""<td>{}</td>""".format(c) for c in self._choices)
        row2 = " ".join("""<td width="75" height="75" style="background-color:{}"></td>""".format(c.rgb) for c in self.colors)
        markdown = """
        **{}** はどれ？
        <table><tr>{}</tr><tr> {}</tr></table>
        """.format(answer, row1, row2)
        return markdown

    def show_question(self):
        markdown = self._question_markdown
        st.markdown(markdown, unsafe_allow_html=True)        
        r = st.radio("", self._choices)
        if st.button("ENTER"):
            self.user_answer = r
            logger.info("User answer is given: %s", self.user_answer)
            index = self._choices.index(self.user_answer)
            _update_history(index == self.answer_index)
            st.experimental_rerun()

    def show_result(self):
        logger.info("User answer: %s", self.user_answer)
        markdown = self._question_markdown
        choices = self._choices
        index = self.user_answer - 1
        items = ["{}. {}（{}, {}, {}）".format(c, col.name, col.reading, col.info, col.rgb) for c,col in zip(choices, self.colors)]
        st.markdown(markdown, unsafe_allow_html=True)
        st.radio("", items, disabled=True, index=index)

        message = "**Goog job!**" if (index == self.answer_index) else "Not correct..."
        message += "　Answer: **{}**".format(choices[self.answer_index])
        st.markdown(message)


class ColorToJIS(Question):
    def __init__(self, n=4):
        self.colors = choose_jis_colors(n)
        self.answer_index = random.randint(0, n-1)
        self.user_answer = None
        logger.info("Colors: %s, answer: %s", self.colors, self.answer_index)

    @property
    def _question_markdown(self):
        rgb = self.colors[self.answer_index].rgb
        markdown = """
        これは何色？
        <table><tr><td width="75" height="75" style="background-color:{}"></td></tr></table>
        """.format(rgb)
        return markdown

    @property
    def _choices(self):
        return ["{}（{}）".format(c.name, c.reading) for c in self.colors]

    def show_question(self):
        markdown = self._question_markdown
        st.markdown(markdown, unsafe_allow_html=True)
        r = st.radio("", self._choices)
        if st.button("ENTER"):
            self.user_answer = r
            logger.info("User answer is given: %s", self.user_answer)
            index = self._choices.index(self.user_answer)
            _update_history(index == self.answer_index)
            st.experimental_rerun()

    def show_result(self):
        logger.info("User answer: %s", self.user_answer)
        markdown = self._question_markdown
        choices = self._choices
        index = choices.index(self.user_answer)
        items = ["{}（{}, {}, {}）".format(col.name, col.reading, col.info, col.rgb) for col in self.colors]
        st.markdown(markdown, unsafe_allow_html=True)
        st.radio("", items, disabled=True, index=index)

        message = "**Goog job!**" if (index == self.answer_index) else "Not correct..."
        message += "　Answer: **{}**".format(choices[self.answer_index])
        st.markdown(message)


def choose_jis_colors(n=4, distinct_rgb=False):
    # pick n jis colors that are close
    x = jis_data()
    
    if distinct_rgb:
        # remove exactly the same RGB
        # shuffle before hand to remove duplicate RGBs randomly
        x = x.sample(frac=1).reset_index(drop=True)
        x = x.drop_duplicates(subset="rgb", keep="first").reset_index(drop=True)

    # choose a color group to ensure some similarity
    # currently, we group by color category
    # we may want to add more variation
    group = random.choice(x.category_color_en)
    logger.info("Group: '%s'", group)
    x = x[x.category_color_en == group]

    tmp = x.sample(n)
    colors = [Color(row.colorname, row.reading, row.rgb, row.feature_word) for _, row in tmp.iterrows()]
    return colors


def _update_history(result): 
    if KEY_ANSWER_HISTORY not in st.session_state:
        st.session_state[KEY_ANSWER_HISTORY] = [result]
    else:
        st.session_state[KEY_ANSWER_HISTORY].append(result)


def generate_question(question_type):
    if question_type == "jis_to_color":
        return JIStoColor()
    elif question_type == "color_to_jis":
        return ColorToJIS()

    return ValueError("Question type not supported: '{}'".format(question_type))