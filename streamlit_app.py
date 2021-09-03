# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import streamlit as st

import pandas as pd
pd.set_option('display.precision', 3)

import io
import json
import dropbox
import streamlit_analytics

from google.cloud import firestore

st.set_page_config(page_title = 'industree',
                   page_icon = ':palm_tree:',
                   layout = 'centered',
                   initial_sidebar_state = 'auto')

firestore_key_dict = json.loads(st.secrets['firestore_key'])
db = firestore.Client.from_service_account_info(firestore_key_dict)


def clear_state(variables):
    """
    Delete variables in session state. Useful when switching tabs.
    - variables (list):
        A list of the names (str) of the variables to be deleted.
    """
    for variable in variables:
        try:
            del st.session_state[variable]
        except:
            pass

@st.cache
def read_alloy_data(resource):
    return pd.read_csv(io.BytesIO(resource.content),
                       sep = ';',
                       header = 0,
                       index_col = 'ID')

def get_frame_double(alloy_data, alloy0, alloy1):
    alloy0_data = alloy_data.loc[alloy0]
    alloy1_data = alloy_data.loc[alloy1]
    temp = pd.DataFrame({'1: ' + alloy0: alloy0_data,
                         '2: ' + alloy1: alloy1_data,
                         'Διαφορά': alloy1_data - alloy0_data},
                        copy = True)
    return temp.style.applymap(lambda x: 'color: orangered' if x < 0
                               else 'color: mediumspringgreen',
                               subset = 'Διαφορά').set_properties(**props)

def get_frame_single(alloy_data, alloy):
    temp = pd.DataFrame({alloy: alloy_data.loc[alloy]}, copy = True)
    return temp.style.set_properties(**props)

def gr_to_en(code):
    greek = {'Α': 'A', 'Β': 'B', 'Ε': 'E', 'Η': 'H', 'Ι': 'I',
         'Κ': 'K', 'Μ': 'M', 'Ν': 'N', 'Ο': 'O', 'Ρ': 'P',
         'Τ': 'T', 'Υ': 'Y', 'Χ': 'X'}
    for grletter, enletter in greek.items():
        code = code.replace(grletter, enletter)
    return code

streamlit_analytics.start_tracking()

page = st.sidebar.selectbox('Εφαρμογή',
                            ['Αλλαγή κράματος', 'Πρόγραμμα παραγωγής'],
                            index = 0,
                            key = 'page')

if page == 'Αλλαγή κράματος':
    clear_state(['schedule_page'])

    st.title('Αλλαγή Κράματος')
    st.markdown('Μια **απλή** εφαρμογή που δίνει πρόσβαση σε πληροφορίες \
                απαραίτητες για την αλλαγή κράματος.')

    password = st.text_input('Κωδικός πρόσβασης',
                             max_chars = 12,
                             key = 'password',
                             type = 'password')
    if password == '':
        st.stop()
    elif not password == st.secrets['password']:
        st.markdown(':red_circle: Λανθασμένος κωδικός!')
        st.stop()

    dbx = dropbox.Dropbox(st.secrets['dropbox_token'])
    res = dbx.files_download("/specs.csv")[1]
    dbx.close()

    alloy_data = read_alloy_data(res)

    props = {'font-size': '11pt'}

    if not st.checkbox('Προβολή δεδομένων για ένα μόνο κράμα'):
        with st.form(key = 'form_double'):
            cols = st.columns([0.45,0.45,0.1])

            help_alloy0 = 'Κωδικός του κράματος που χυτεύεται έως τώρα'
            with cols[0]:
                alloy0 = st.selectbox('Τρέχον κράμα',
                                      alloy_data.index,
                                      key = 'alloy0',
                                      help = help_alloy0)

                btn_refresh = st.form_submit_button('Προβολή επιλογών')

            help_alloy1 = 'Κωδικός του κράματος που πρόκειται να χυτευτεί'
            with cols[1]:
                alloy1 = st.selectbox('Επόμενο κράμα',
                                      alloy_data.index,
                                      key = 'alloy1',
                                      help = help_alloy1)

                btn_reverse = st.form_submit_button('Αντίστροφη προβολή')

            if btn_refresh:
                st.dataframe(get_frame_double(alloy_data, alloy0, alloy1))
            if btn_reverse:
                st.dataframe(get_frame_double(alloy_data, alloy1, alloy0))

    else:
        with st.form(key = 'form_single'):
            cols = st.columns([0.45,0.45,0.1])

            with cols[0]:
                alloy = st.selectbox('Κράμα',
                                      alloy_data.index,
                                      key = 'alloy')

            if st.form_submit_button('Προβολή επιλογής'):
                st.dataframe(get_frame_single(alloy_data, alloy))

elif page == 'Πρόγραμμα παραγωγής':
    st.title('Πρόγραμμα παραγωγής')
    st.markdown('Μια **ελαφρώς σύνθετη** εφαρμογή που επιτρέπει την προβολή \
                και την τροποποίηση του προγράμματος παραγωγής.')

    schedule_functions = ['Πίνακες παραγγελιών', 'Προσθήκη παραγγελίας',
                          'Τροποποίηση παραγγελίας', 'Διαγραφή παραγγελίας']
    schedule_page = st.sidebar.selectbox('Λειτουργία',
                                         schedule_functions,
                                         key = 'schedule_page')

    add_variables = ['add_section', 'add_table', 'add_code', 'add_position',
                     'add_quantity', 'add_pending', 'add_start_date',
                     'add_trial']

    edit_variables = ['init_section', 'init_position', 'edit_table',
                      'edit_section', 'edit_code', 'edit_position',
                      'edit_quantity', 'edit_pending', 'edit_start_date',
                      'new_section', 'new_code', 'new_position',
                      'new_quantity', 'new_pending', 'new_start_date']

    delete_variables = ['delete_section', 'delete_table', 'delete_position']

    orders_list = list(db.collection('orders').stream())
    orders_dict = list(map(lambda x: x.to_dict(), orders_list))
    orders = pd.DataFrame(orders_dict,
                          columns = ['section', 'position', 'code', 'quantity',
                                     'pending', 'start_date', 'trial'])
    orders.columns = ['Εγκατάσταση', 'Θέση', 'Κωδικός', 'Πλήθος', 'Υπόλοιπο',
                      'Έναρξη καμπάνιας', 'Δοκιμή']

    if schedule_page == "Πίνακες παραγγελιών":
        clear_state(add_variables + edit_variables + delete_variables)

        st.header(schedule_page)

        for x in ['Α', 'Β', 'Η', 'Θ']:
            st.markdown('### Εγκατάσταση **{}**'.format(x))
            show_table = orders.query("Εγκατάσταση == '{}'".format(x))\
                .sort_values(by = 'Θέση', ignore_index = True)
            st.dataframe(show_table)

    elif schedule_page == 'Προσθήκη παραγγελίας':
        clear_state(edit_variables + delete_variables)

        st.header(schedule_page)

        add_cols_aux = st.columns([0.32, 0.7])
        with add_cols_aux[0]:
            add_section = st.selectbox('Εγκατάσταση',
                                       ['Α', 'Β', 'Η', 'Θ'],
                                       key = 'add_section')

        with st.expander('Πίνακας παραγγελιών'):
            add_table = orders.query("Εγκατάσταση == '{}'".format(add_section))\
                .sort_values(by = 'Θέση', ignore_index = True)
            st.dataframe(add_table)

        with st.form(key = 'add_form'):
            add_cols = st.columns([0.3, 0.3, 0.3, 0.1])

            with add_cols[0]:
                help_add_code = 'Κωδικός του κράματος που ζητείται να χυτευτεί'
                add_code = st.text_input('Κωδικός',
                                         key = 'add_code',
                                         help = help_add_code).upper()
                add_code = gr_to_en(add_code)

                default = orders.query("Εγκατάσταση == @add_section")['Θέση'].max() + 1
                default = default if (isinstance(default, int)) else 1

                help_add_position = 'Θέση της νέας χύτευσης στο πρόγραμμα'
                add_position = st.number_input('Θέση',
                                               min_value = 1,
                                               max_value = 99,
                                               value = default,
                                               key = 'add_position',
                                               help = help_add_position)

            with add_cols[1]:
                help_add_quantity = 'Ποσότητα που ζητείται να χυτευτεί σε πλήθος πλακών/κολονών'
                add_quantity = st.number_input('Ποσότητα',
                                               min_value = 1,
                                               max_value = 99,
                                               key = 'add_quantity',
                                               help = help_add_quantity)

                help_add_start_date = 'Ημέρα μετά την οποία ζητείται να εκτελεστεί η παραγγελία'
                add_start_date = st.date_input('Έναρξη καμπάνιας',
                                               key = 'add_start_date',
                                               help = help_add_start_date)

            with add_cols[2]:
                help_add_pending = 'Πλήθος πλακών/κολονών που εκκρεμεί να χυτευτούν'
                add_pending = st.number_input('Υπόλοιπο',
                                              min_value = 0,
                                              max_value = 99,
                                              key = 'add_pending',
                                              help = help_add_pending)
            help_trial = 'Επιλέξτε αν η χύτευση είναι δοκιμαστική'
            add_trial = st.checkbox('Δοκιμή',
                                    value = False,
                                    key = 'add_trial',
                                    help = help_trial)

            if st.form_submit_button('Προσθήκη'):

                max_add_position = orders.query("Εγκατάσταση == @add_section")['Θέση'].max()
                if add_position > max_add_position + 1:
                    st.markdown(':red_circle: Οι θέσεις στη σειρά χύτευσης πρέπει να είναι διαδοχικές!')
                elif add_pending > add_quantity:
                    st.markdown(':red_circle: Το υπόλοιπο χυτεύσεων δεν πρέπει να είναι μεγαλύτερο της συνολικής ποσότητας!')
                else:
                    batch = db.batch()

                    for doc in db.collection('orders').\
                        where('section', '==', add_section).stream():
                        old_position = doc.get('position')
                        if old_position >= add_position:
                            new_position = old_position + 1
                            batch.update(doc.reference,
                                         {'position': new_position})

                    batch.commit()

                    doc_ref = db.collection('orders').document()
                    doc_ref.set({'section': add_section,
                                 'position': add_position,
                                 'code': add_code,
                                 'quantity': add_quantity,
                                 'pending': add_pending,
                                 'trial': add_trial,
                                 'start_date': add_start_date.strftime('%Y/%m/%d')})

                    st.markdown(':white_check_mark: Η παραγγελία προστέθηκε επιτυχώς!')
                    st.markdown(':grey_exclamation: Η μεταβολή θα εμφανιστεί στον πίνακα όταν η σελίδα ανανεωθεί.')

    elif schedule_page == 'Τροποποίηση παραγγελίας':
        clear_state(add_variables + delete_variables)

        st.header(schedule_page)

        edit_cols_aux = st.columns([0.32, 0.7])

        with edit_cols_aux[0]:
            init_section = st.selectbox('Εγκατάσταση',
                                        ['Α', 'Β', 'Η', 'Θ'],
                                        key = 'init_section')

        with st.expander('Πίνακας παραγγελιών'):
            edit_table = orders.query("Εγκατάσταση == '{}'".format(init_section))\
                .sort_values(by = 'Θέση', ignore_index = True)
            st.dataframe(edit_table)

        with st.form(key = 'edit_form'):
            edit_cols_aux2 = st.columns([0.32, 0.7])

            with edit_cols_aux2[0]:
                help_init_position = 'Θέση της χύτευσης στο πρόγραμμα'
                init_position = st.number_input('Θέση',
                                                min_value = 1,
                                                max_value = 99,
                                                step = 1,
                                                key = 'init_position',
                                                help = help_init_position)

            st.markdown('')
            edit_cols = st.columns([0.40, 0.1, 0.40, 0.1])

            with edit_cols[0]:
                edit_section = st.checkbox('Τροποποίηση εγκατάστασης;',
                                            key = 'edit_section',
                                            value = False)
                new_section = st.selectbox('Εγκατάσταση',
                                           ['Α', 'Β', 'Η', 'Θ'],
                                           key = 'new_section')

                edit_code = st.checkbox('Τροποποίηση κωδικού;',
                                        key = 'edit_code')
                new_code = st.text_input('Νέος Κωδικός',
                                         key = 'new_code').upper()
                new_code = gr_to_en(new_code)

                edit_quantity = st.checkbox('Τροποποίηση ποσότητας;',
                                            key = 'edit_quantity')
                new_quantity = st.number_input('Νέα ποσότητα',
                                               min_value = 1,
                                               max_value = 99,
                                               key = 'new_quantity')
                st.markdown('')
                edit_trial = True
                new_trial = st.checkbox('Τροποποιημένη κατάσταση δοκιμής',
                                        value = False,
                                        key = 'new_trial')

            with edit_cols[2]:
                edit_position = st.checkbox('Τροποποίηση θέσης;',
                                            key = 'edit_position')
                new_position = st.number_input('Νεα θέση',
                                               min_value = 1,
                                               max_value = 99,
                                               key = 'new_position')

                edit_start_date = st.checkbox('Τροποποίηση έναρξης',
                                              key = 'edit_start_date')
                new_start_date = st.date_input('Νέα έναρξη καμπάνιας',
                                               key = 'new_start_date')

                edit_pending = st.checkbox('Τροποποίηση υπολοίπου;',
                                           key = 'edit_pending')
                new_pending = st.number_input('Νέο υπόλοιπο',
                                              min_value = 0,
                                              max_value = 99,
                                              key = 'new_pending')

            checkboxes = [edit_section, edit_code, edit_position, edit_quantity,
                          edit_pending, edit_start_date, edit_trial]

            new_values = [{'section': new_section},
                          {'code': new_code},
                          {'position': new_position},
                          {'quantity': new_quantity},
                          {'pending': new_pending},
                          {'start_date': new_start_date},
                          {'trial': new_trial}]

            if st.form_submit_button('Τροποποίηση'):

                max_init_position = orders.query("Εγκατάσταση == @init_section")['Θέση'].max()
                max_new_position = orders.query("Εγκατάσταση == @new_section")['Θέση'].max()

                if init_position > max_init_position:
                    st.markdown(':red_circle: Δεν υπάρχει χύτευση με αυτό τον αριθμό θέσης!')

                elif (edit_section and not edit_position):
                    st.markdown(':red_circle: Για τροποποίηση εγκατάστασης πρέπει να επιλεγεί και η τροποποίηση θέσης, καθώς και να οριστεί σωστά η θέση στη νέα εγκατάσταση.')

                elif (edit_section and new_position > max_new_position + 1):
                    st.markdown(':red_circle: Οι θέσεις στη σειρά χύτευσης πρέπει να είναι διαδοχικές!')

                elif (not edit_section and edit_position and init_position == new_position):
                    st.markdown(':red_circle: Η νέα θέση δεν πρέπει να είναι ίδια με την αρχική!')

                elif (not edit_section and edit_position and new_position > max_init_position + 1):
                    st.markdown(':red_circle: Οι θέσεις στη σειρά χύτευσης πρέπει να είναι διαδοχικές!')

                else:
                    if edit_section:
                        batch = db.batch()
                        for doc in db.collection('orders').\
                            where('section', '==', new_section).stream():
                            doc_position = doc.get('position')
                            if doc_position >= new_position:
                                move_position = doc_position + 1
                                batch.update(doc.reference,
                                             {'position': move_position})
                        batch.commit()

                        batch = db.batch()
                        for doc in db.collection('orders').\
                            where('section', '==', init_section).stream():
                            if doc.get('position') == init_position:
                                for (checkbox, value) in zip(checkboxes, new_values):
                                    if checkbox:
                                        batch.update(doc.reference, value)
                        batch.commit()

                        batch = db.batch()
                        for doc in db.collection('orders').\
                            where('section', '==', init_section).stream():
                            doc_position = doc.get('position')
                            if doc_position >= init_position:
                                move_position = doc_position - 1
                                batch.update(doc.reference,
                                             {'position': move_position})
                        batch.commit()

                    elif edit_position:
                        batch = db.batch()
                        for doc in db.collection('orders').\
                            where('section', '==', init_section).stream():
                            doc_position = doc.get('position')
                            if doc_position == init_position:
                                batch.update(doc.reference, {'section': 'Ω'})
                        batch.commit()

                        batch = db.batch()
                        if new_position < init_position:
                            for doc in db.collection('orders').\
                                where('section', '==', init_section).stream():
                                doc_position = doc.get('position')
                                if (doc_position < init_position and doc_position >= new_position):
                                    move_position = doc_position + 1
                                    batch.update(doc.reference, {'position': move_position})
                            batch.commit()

                            ## batch = db.batch()
                        else:
                            batch = db.batch() ##
                            for doc in db.collection('orders').\
                                where('section', '==', init_section).stream():
                                doc_position = doc.get('position')
                                if (doc_position > init_position and doc_position <= new_position):
                                    move_position = doc_position - 1
                                    batch.update(doc.reference, {'position': move_position})
                            batch.commit()

                        batch = db.batch()
                        for doc in db.collection('orders').\
                            where('section', '==', 'Ω').stream():
                            for (checkbox, value) in zip(checkboxes[1:], new_values[1:]):
                                if checkbox:
                                    batch.update(doc.reference, value)
                            batch.update(doc.reference, {'section': init_section})
                        batch.commit()

                    else:
                        batch = db.batch()
                        for doc in db.collection('orders').\
                            where('section', '==', init_section).stream():
                            doc_position = doc.get('position')
                            if doc_position == init_position:
                                for (checkbox, value) in zip(checkboxes, new_values):
                                    if checkbox:
                                        batch.update(doc.reference, value)
                        batch.commit()

                    st.markdown(':white_check_mark: Η παραγγελία τροποποιήθηκε επιτυχώς!')
                    st.markdown(':grey_exclamation: Η μεταβολή θα εμφανιστεί \
                                στον πίνακα όταν η σελίδα ανανεωθεί.')

    elif schedule_page == 'Διαγραφή παραγγελίας':
        clear_state(add_variables + edit_variables)

        st.header(schedule_page)

        delete_cols_aux = st.columns([0.32, 0.7])
        with delete_cols_aux[0]:
            delete_section = st.selectbox('Εγκατάσταση',
                                          ['Α', 'Β', 'Η', 'Θ'],
                                          key = 'delete_section')

        with st.expander('Πίνακας παραγγελιών'):
            delete_empty = st.empty()
            delete_table = orders.query("Εγκατάσταση == '{}'".format(delete_section))\
                .sort_values(by = 'Θέση', ignore_index = True)
            delete_empty.dataframe(delete_table)

        with st.form(key = 'delete_form'):
            delete_cols = st.columns([0.32, 0.32, 0.36])

            with delete_cols[0]:
                help_delete_position = 'Θέση της χύτευσης στο πρόγραμμα'
                delete_position = st.number_input('Θέση',
                                                  min_value = 1,
                                                  max_value = 99,
                                                  key = 'delete_position',
                                                  help = help_delete_position)

            if st.form_submit_button('Διαγραφή'):

                max_delete_position = orders.query("Εγκατάσταση == @delete_section")['Θέση'].max()
                if delete_position > max_delete_position:
                    st.markdown(':red_circle: Δεν υπάρχει χύτευση με αυτό τον αριθμό θέσης!')
                else:
                    batch = db.batch()
                    for doc in db.collection('orders').\
                        where('section', '==', delete_section).stream():
                        old_position = doc.get('position')
                        if old_position == delete_position:
                            batch.delete(doc.reference)
                        else:
                            if old_position >= delete_position:
                                new_position = old_position - 1
                                batch.update(doc.reference, {'position': new_position})
                    batch.commit()

                    st.markdown(':white_check_mark: Η παραγγελία διαγράφηκε επιτυχώς!')
                    st.markdown(':grey_exclamation: Η μεταβολή θα εμφανιστεί \
                                στον πίνακα όταν η σελίδα ανανεωθεί.')

streamlit_analytics.stop_tracking()
