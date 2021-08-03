# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import streamlit as st

st.set_page_config(page_title = 'industree',
                   page_icon = ':palm_tree:',
                   layout = 'centered',
                   initial_sidebar_state = 'auto')

st.title('Αλλαγή Κράματος') # 'Alloy Change'

st.markdown('Μια **απλή** εφαρμογή που δίνει πρόσβαση σε πληροφορίες απαραίτητες \
            για την αλλαγή κράματος.')

password = st.text_input('Κωδικός πρόσβασης',
                         max_chars = 12,
                         key = 'password',
                         type = 'password')

if not password == st.secrets['password']: st.stop()

st.write('Ο κωδικός είναι σωστός!')
