# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import streamlit as st

import io
import dropbox
import streamlit_analytics
import pandas as pd

pd.set_option('display.precision', 3)

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

if password == '':
    st.stop()
elif not password == st.secrets['password']:
    st.markdown(':red_circle: Λανθασμένος κωδικός!')
    st.stop()

streamlit_analytics.start_tracking()

dbx = dropbox.Dropbox(st.secrets['dropbox_token'])
res = dbx.files_download("/specs.csv")[1]
dbx.close()

@st.cache
def read_data(res):
    return pd.read_csv(io.BytesIO(res.content),
                       sep = ';',
                       header = 0,
                       index_col = 'ID')

data = read_data(res)

props = {'font-size': '11pt'}

def get_frame_double(alloy0, alloy1):
    temp = pd.DataFrame({'1: ' + alloy0: data.loc[alloy0],
                         '2: ' + alloy1: data.loc[alloy1],
                         'Διαφορά': data.loc[alloy1] - data.loc[alloy0]},
                        copy = True)
    return temp.style.applymap(lambda x: 'color: orangered' if x < 0
                               else 'color: mediumspringgreen',
                               subset = 'Διαφορά')\
                     .set_properties(**props)

def get_frame_single(alloy):
    temp = pd.DataFrame({alloy: data.loc[alloy]}, copy = True)
    return temp.style.set_properties(**props)


if not st.checkbox('Προβολή δεδομένων για ένα μόνο κράμα'):
    with st.form(key = 'form_double'):
        cols = st.beta_columns([0.45,0.45,0.1])

        help_alloy0 = 'Κωδικός του κράματος που χυτεύεται έως τώρα'
        with cols[0]:
            alloy0 = st.selectbox('Τρέχον κράμα',
                                  data.index,
                                  index = 0,
                                  key = 'alloy0',
                                  help = help_alloy0)

        help_alloy1 = 'Κωδικός του κράματος που πρόκειται να χυτευτεί'
        with cols[1]:
            alloy1 = st.selectbox('Επόμενο κράμα',
                                  data.index,
                                  index = 0,
                                  key = 'alloy1',
                                  help = help_alloy1)

        btn_cols = st.beta_columns([0.3,0.3,0.4])

        with btn_cols[0]:
            btn_refresh = st.form_submit_button('Προβολή επιλογών')
        with btn_cols[1]:
            btn_reverse = st.form_submit_button('Αντίστροφη προβολή')

        if btn_refresh:
            st.dataframe(get_frame_double(alloy0, alloy1))
        if btn_reverse:
            st.dataframe(get_frame_double(alloy1, alloy0))

else:
    with st.form(key = 'form_single'):
        cols = st.beta_columns([0.45,0.45,0.1])

        with cols[0]:
            alloy = st.selectbox('Κράμα',
                                 data.index,
                                 index = 0,
                                 key = 'alloy')

        if st.form_submit_button('Προβολή επιλογής'):
            st.dataframe(get_frame_single(alloy))

streamlit_analytics.stop_tracking()
