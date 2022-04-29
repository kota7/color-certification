# -*- coding: utf-8 -*-

import sqlite3
import math
from contextlib import contextmanager
from logging import getLogger
from collections import namedtuple
from unicodedata import name
import pandas as pd
import streamlit as st
logger = getLogger(__file__)

def _euclid_dist(x1, x2, x3, y1, y2, y3):
    return ((x1-y1)**2 + (x2-y2)**2 + (x3-y3)**2)**0.5

@contextmanager
def _connect():
    conn = sqlite3.connect("colors.db")
    #conn.create_function("euclid_dist", 6, _euclid_dist, deterministic=True)  # version diff?
    conn.create_function("euclid_dist", 6, _euclid_dist)
    try:
        yield conn
    finally:
        conn.close()

def _init_state_if_not_exist(key: str, value):
    if key not in st.session_state:
        st.session_state[key] = value

def _set_state(key, value):
    st.session_state[key] = value


def _set_question():
    q = """
    with tmp AS (
      SELECT name, munsell, rgb, r, g, b, row_number() OVER (ORDER BY random()) AS rn FROM colors WHERE colortype='jis' )
    ,ans AS (
      SELECT name, munsell, rgb, r, g, b FROM tmp WHERE rn=1
    )
    ,cand AS (
      SELECT
        x.name, x.munsell, x.rgb, 
        euclid_dist(x.R, x.G, x.B, y.R, y.G, y.B) / 3.0 AS dist, 
        row_number() OVER (ORDER BY random()) AS rn
      FROM 
        colors AS x, ans AS y
      WHERE
        x.colortype='jis'
        AND x.name <> y.name AND x.rgb <> y.rgb
        AND euclid_dist(x.R, x.G, x.B, y.R, y.G, y.B) / 3.0 BETWEEN 1 AND 40
    )
    SELECT name, munsell, rgb, 1 AS answer, NULL AS dist FROM ans
    UNION ALL
    SELECT name, munsell, rgb, 0 AS answer, dist FROM cand WHERE rn <= 3
    """
    with _connect() as conn:
        res = pd.read_sql(q, conn)
    res = res.sample(frac=1)
    print(res)
    answer = res[res.answer==1].name.item()
    names = res.name.tolist()

    markdown = """
    **{}** はどれ？
    <table>
    <tr> <td>1</td> <td>2</td> <td>3</td> <td>4</td></tr>
    <tr> <td width="75" height="75" style="background-color:{}"></td>
         <td width="75" height="75" style="background-color:{}"></td>
         <td width="75" height="75" style="background-color:{}"></td>
         <td width="75" height="75" style="background-color:{}"></td></tr>
    </table>
    """.format(answer, *res.rgb)
    choices = [1,2,3,4]
    correct = res.name.tolist().index(answer) + 1
    st.session_state["question"] = (markdown, choices, correct, names)
    st.session_state["givenAnswer"] = None 

def _show_question(container=st):
    q = st.session_state.get("question")
    if q is None:
        logger.info("Question is not set yet")
        return

    markdown, choices, correct, names = q
    container.markdown(markdown, unsafe_allow_html=True)
    user_answer = container.radio("", choices)
    button = container.button("ENTER")
    if button:
       _set_state("givenAnswer", user_answer)
       st.experimental_rerun()

def _show_answer(container=st):
    q = st.session_state.get("question")
    if q is None:
        logger.info("Question is not set yet")
        return
    markdown, choices, correct, names = q
    given_answer = st.session_state.get("givenAnswer")
    index = 0 if given_answer is None else choices.index(given_answer)
    container.markdown(markdown, unsafe_allow_html=True)
    container.radio("", ["{}. {}".format(c, n) for c, n in zip(choices, names)], disabled=True, index=index)
    if given_answer == correct:
        container.markdown("**Goog job!**")
    else:
        container.markdown("Not correct. Keep learning!")

def main():
    _init_state_if_not_exist("question", None)
    _init_state_if_not_exist("givenAnswer", None)
    question_part = st.container()
    if st.session_state["givenAnswer"] is None:
        _show_question(question_part)
    else:
        _show_answer(question_part)
    st.button("Next question", on_click=_set_question)
    

if __name__ == "__main__":
    main()