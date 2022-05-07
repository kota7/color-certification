# -*- coding: utf-8 -*-

import random
from logging import getLogger
import streamlit as st
from questions import generate_question, KEY_ANSWER_HISTORY
logger = getLogger(__file__)

# state variable names
KEY_QUESTION = "currentQuestion"

def _current_question():
    return st.session_state.get(KEY_QUESTION)

def main():
    def _update_question():
        question_weights = {"jis_to_color": jis_to_color, "color_to_jis": color_to_jis}
        types = list(question_weights)
        weights = list(question_weights.values())
        if sum(weights) == 0:
            weights = [1] * len(types)  # when all weights are zero, assign equal probabilities
            
        logger.info("Question weight: %s, %s", types, weights)
        question_type = random.choices(types, weights, k=1)[0]
        logger.info("Question type: '%s'", question_type)
        q = generate_question(question_type)
        st.session_state[KEY_QUESTION] = q
        st.experimental_rerun()


    with st.sidebar:
        st.write("問題の種類を選択（数値が高いものほど多く出題されます）")
        jis_to_color = st.slider("慣用色名 → 色", 0, 10, 10, key="jis_to_color")
        color_to_jis = st.slider("色 → 慣用色名", 0, 10, 10, key="color_to_jis")
        
        total_weights = jis_to_color + color_to_jis
        if total_weights == 0:
            st.warning("All weights are zero. All types are generated with equal probability")

    q = _current_question()
    if q is None:
        # no question generated, show the start button
        if st.button("START"):
            _update_question()
    else:
        if q.user_answer is None:
            # question exists, but it has not been answered
            # show the elements for user to answer
            q.show_question()
        else:
            # question has been answered
            # show the result
            q.show_result()
            if st.button("NEXT"):
                _update_question()
                st.experimental_rerun()

    if KEY_ANSWER_HISTORY in st.session_state:
        results = st.session_state[KEY_ANSWER_HISTORY]   
        correct = sum(results)
        n = len(results)
        st.markdown("正答率 %d / %d (%.1f %%)" % (correct, n, correct*100/n))

if __name__ == "__main__":
    main()