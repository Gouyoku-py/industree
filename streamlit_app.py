# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import streamlit as st

import pandas as pd
pd.set_option('display.precision', 3)

import json
import streamlit_analytics

from string import Template
from google.cloud import firestore

st.set_page_config(page_title = 'industree',
                   page_icon = ':palm_tree:',
                   layout = 'wide',
                   initial_sidebar_state = 'auto')

firestore_key = json.loads(st.secrets['firestore_key'])
db = firestore.Client.from_service_account_info(firestore_key)

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
def read_alloy_data():
    return pd.read_csv('gs://industree-py.appspot.com/specs.csv',
                       sep = ';',
                       header = 0,
                       index_col = 'ID',
                       storage_options = {'token': firestore_key})

@st.cache
def read_products_data():
    col_names = ['Κωδικός', 'Είδος', 'Διαστάσεις', 'Κράμα', 'Επεξεργασία',
                 'Πλήθος', 'Μήκος', 'Ανοχές', 'Βάρος', 'Πελάτης']
    products = pd.read_csv('gs://industree-py.appspot.com/products.csv',
                           sep = ';',
                           header = None,
                           names = col_names,
                           usecols = [i for i in range(9)] + [10],
                           encoding = 'utf-8',
                           storage_options = {'token': firestore_key})
    products['Διαστάσεις'] = products['Διαστάσεις'].apply(lambda x: x.replace('X', 'x'))
    return products

@st.cache
def read_crc_data():
    crc = pd.read_csv('gs://industree-py.appspot.com/crc.csv',
                      sep = ',',
                      header = 0,
                      encoding = 'utf-8',
                      storage_options = {'token': firestore_key})
    crc['Διαστάσεις'] = crc['Διαστάσεις'].apply(str)
    crc['Κουτιά'] = crc['Κουτιά'].apply(lambda x: x.split(';'))
    crc.set_index('Διαστάσεις', drop = True, append = False, inplace = True)
    return crc

def read_orders_data():
    orders_list = list(db.collection('orders').stream())
    orders_dict = list(map(lambda x: x.to_dict(), orders_list))
    orders = pd.DataFrame(orders_dict,
                          columns = ['section', 'position', 'code', 'quantity',
                                     'pending', 'start_date', 'due_date',
                                     'trial', 'crc'])
    orders.columns = ['Εγκατάσταση', 'Θέση', 'Κωδικός', 'Πλήθος', 'Υπόλοιπο',
                      'Έναρξη καμπάνιας', 'Προθεσμία καμπάνιας', 'Δοκιμή', 'CRC']
    return orders

def read_scrap_data():
    scrap_list = list(db.collection('scrap').stream())
    scrap_dict = list(map(lambda x: x.to_dict(), scrap_list))
    return pd.DataFrame(scrap_dict)

def get_orders_csv(orders):
    orders_csv = orders.sort_values(by = ['Εγκατάσταση', 'Θέση'],
                                    ignore_index = True)
    return orders_csv.to_csv(index = False, encoding = 'utf-8')

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

@st.cache
def get_var_lists():
    add_vars = ['add_section', 'add_table', 'add_position', 'add_code',
                'add_quantity', 'add_pending', 'add_start_date', 'add_due_date'
                'add_crc', 'add_trial']
    edit_vars = ['init_section', 'init_position', 'edit_table',
                 'edit_section', 'edit_position', 'edit_code',
                 'edit_quantity', 'edit_pending', 'edit_start_date', 'edit_due_date',
                 'edit_crc', 'new_section', 'new_code', 'new_position',
                 'new_quantity', 'new_pending', 'new_start_date', 'new_due_date',
                 'new_crc']
    delete_vars = ['delete_section', 'delete_table', 'delete_position']
    scrap_vars = ['scrap_section', 'scrap_entry', 'scrap_text']
    sections = ['Α', 'Β', 'Η', 'Θ']
    return add_vars, edit_vars, delete_vars, scrap_vars, sections

streamlit_analytics.start_tracking()

password = st.sidebar.text_input('Κωδικός πρόσβασης',
                                 max_chars = 12,
                                 key = 'password',
                                 type = 'password')
if password == '':
    st.stop()
elif not password == st.secrets['password']:
    st.markdown(':red_circle: Λανθασμένος κωδικός!')
    st.stop()

page = st.sidebar.selectbox('Εφαρμογή',
                            ['Αλλαγή Κράματος', 'Πρόγραμμα Παραγωγής'],
                            index = 0,
                            key = 'page')

if page == 'Αλλαγή Κράματος':
    clear_state(['schedule_page'])

    st.title(page)
    st.markdown('Μια **απλή** εφαρμογή που δίνει πρόσβαση σε πληροφορίες \
                απαραίτητες για την αλλαγή κράματος.')

    alloy_data = read_alloy_data()

    props = {'font-size': '11pt'}

    if not st.checkbox('Προβολή δεδομένων για ένα μόνο κράμα'):
        with st.form(key = 'form_double'):
            alloy_cols0 = st.columns([0.45,0.45,0.1])

            help_alloy0 = 'Κωδικός του κράματος που χυτεύεται έως τώρα'
            with alloy_cols0[0]:
                alloy0 = st.selectbox('Τρέχον κράμα',
                                      alloy_data.index,
                                      key = 'alloy0',
                                      help = help_alloy0)

            help_alloy1 = 'Κωδικός του κράματος που πρόκειται να χυτευτεί'
            with alloy_cols0[1]:
                alloy1 = st.selectbox('Επόμενο κράμα',
                                      alloy_data.index,
                                      key = 'alloy1',
                                      help = help_alloy1)

            alloy_cols1 = st.columns([0.45,0.45,0.1])

            with alloy_cols1[0]:
                btn_refresh = st.form_submit_button('Προβολή επιλογών')
            with alloy_cols1[1]:
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

elif page == 'Πρόγραμμα Παραγωγής':
    st.title(page)
    st.markdown('Μια **ελαφρώς σύνθετη** εφαρμογή που επιτρέπει την προβολή \
                και την τροποποίηση του προγράμματος παραγωγής.')

    products_data = read_products_data()

    schedule_functions = ['Παραγγελίες', 'Προσθήκη παραγγελίας',
                          'Τροποποίηση παραγγελίας', 'Διαγραφή παραγγελίας',
                          'Καταχώρηση scrap', 'Στοιχεία προϊόντων']
    schedule_page = st.sidebar.selectbox('Λειτουργία',
                                         schedule_functions,
                                         key = 'schedule_page')

    add_vars, edit_vars, delete_vars, scrap_vars, sections = get_var_lists()

    orders = read_orders_data()
    scrap = read_scrap_data()
    crc = read_crc_data()

    crc_unique = set([item for sublist in crc['Κουτιά'].to_list() for item in sublist])
    crc_unique_sorted = list(crc_unique)
    crc_unique_sorted.sort()

    today = pd.to_datetime('today').strftime('%d-%m-%Y')
    if st.sidebar.download_button('Λήψη προγράμματος (csv)',
                                  data = get_orders_csv(orders),
                                  file_name = 'Production_Schedule_{}.csv'.format(today),
                                  key = 'download_schedule'):
        help_download = 'Κατεβάστε το αρχείο στον υπολογιστή σας και εισάγετέ το σε ένα κενό φύλλο του Excel, επιλέγοντας κωδικοποίηση UTF-8.'
        st.sidebar.markdown(help_download)

    if schedule_page == 'Προσθήκη παραγγελίας':
        clear_state(edit_vars + delete_vars + scrap_vars)

        st.header(schedule_page)

        add_cols0 = st.columns([0.32, 0.68])
        with add_cols0[0]:
            add_section = st.selectbox('Εγκατάσταση',
                                       sections,
                                       key = 'add_section')

        with st.expander('Πίνακας παραγγελιών'):
            add_table = orders.query("Εγκατάσταση == '{}'".format(add_section))\
                .sort_values(by = 'Θέση', ignore_index = True)
            st.dataframe(add_table)

        with st.form(key = 'add_form'):
            add_cols1 = st.columns([0.3, 0.3, 0.3, 0.1])

            with add_cols1[0]:
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

                help_add_crc = 'CRC που απαιτείται να χρησιμοποιηθεί για τη χύτευση'
                add_crc = st.selectbox('CRC',
                                       ['N/A'] + crc_unique_sorted,
                                       key = 'add_crc',
                                       help = help_add_crc)

            with add_cols1[1]:
                help_add_quantity = 'Ποσότητα που ζητείται να χυτευτεί σε πλήθος πλακών/κολονών'
                add_quantity = st.number_input('Ποσότητα',
                                               min_value = 1,
                                               max_value = 99,
                                               key = 'add_quantity',
                                               help = help_add_quantity)

                help_add_start_date = 'Ημέρα από την οποία ζητείται να εκτελεστεί η παραγγελία'
                add_start_date = st.date_input('Έναρξη καμπάνιας',
                                               key = 'add_start_date',
                                               help = help_add_start_date)

            with add_cols1[2]:
                help_add_pending = 'Πλήθος πλακών/κολονών που εκκρεμεί να χυτευτούν'
                add_pending = st.number_input('Υπόλοιπο',
                                              min_value = 0,
                                              max_value = 99,
                                              key = 'add_pending',
                                              help = help_add_pending)

                help_add_due_date = 'Ημέρα έως την οποία ζητείται να εκτελεστεί η παραγγελία'
                add_due_date = st.date_input('Προθεσμία καμπάνιας',
                                             key = 'add_due_date',
                                             help = help_add_due_date)

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
                    set_dict = {'section': add_section,
                                'position': add_position,
                                'code': add_code,
                                'quantity': add_quantity,
                                'pending': add_pending,
                                'trial': add_trial,
                                'start_date': add_start_date.strftime('%Y/%m/%d'),
                                'due_date': add_due_date.strftime('%Y/%m/%d'),
                                'crc': add_crc}
                    doc_ref.set(set_dict)

                    st.markdown(':white_check_mark: Η παραγγελία προστέθηκε επιτυχώς!')
                    st.markdown(':grey_exclamation: Η μεταβολή θα εμφανιστεί στον πίνακα όταν η σελίδα ανανεωθεί.')

    elif schedule_page == 'Τροποποίηση παραγγελίας':
        clear_state(add_vars + delete_vars + scrap_vars)

        st.header(schedule_page)

        edit_cols0 = st.columns([0.32, 0.68])

        with edit_cols0[0]:
            init_section = st.selectbox('Εγκατάσταση',
                                        sections,
                                        key = 'init_section')

        with st.expander('Πίνακας παραγγελιών'):
            edit_table = orders.query("Εγκατάσταση == '{}'".format(init_section))\
                .sort_values(by = 'Θέση', ignore_index = True)
            st.dataframe(edit_table)

        with st.form(key = 'edit_form'):
            edit_cols1 = st.columns([0.32, 0.68])

            with edit_cols1[0]:
                help_init_position = 'Θέση της χύτευσης στο πρόγραμμα'
                init_position = st.number_input('Θέση',
                                                min_value = 1,
                                                max_value = 99,
                                                step = 1,
                                                key = 'init_position',
                                                help = help_init_position)

            st.markdown('')
            edit_cols2 = st.columns([0.40, 0.1, 0.40, 0.1])

            with edit_cols2[0]:
                edit_section = st.checkbox('Τροποποίηση εγκατάστασης;',
                                           key = 'edit_section',
                                           value = False)
                new_section = st.selectbox('Εγκατάσταση',
                                           sections,
                                           key = 'new_section')

                edit_quantity = st.checkbox('Τροποποίηση ποσότητας;',
                                            key = 'edit_quantity')
                new_quantity = st.number_input('Νέα ποσότητα',
                                               min_value = 1,
                                               max_value = 99,
                                               key = 'new_quantity')

                edit_start_date = st.checkbox('Τροποποίηση έναρξης',
                                              key = 'edit_start_date')
                new_start_date = st.date_input('Νέα έναρξη καμπάνιας',
                                               key = 'new_start_date')

                edit_crc = st.checkbox('Τροποποίηση CRC;',
                                       key = 'edit_crc')
                new_crc = st.selectbox('CRC',
                                       ['N/A'] + crc_unique_sorted,
                                       key = 'new_crc')

                st.markdown('')
                edit_trial = True
                new_trial = st.checkbox('Τροποποιημένη κατάσταση δοκιμής',
                                        value = False,
                                        key = 'new_trial')

            with edit_cols2[2]:
                edit_position = st.checkbox('Τροποποίηση θέσης;',
                                            key = 'edit_position')
                new_position = st.number_input('Νεα θέση',
                                               min_value = 1,
                                               max_value = 99,
                                               key = 'new_position')

                edit_pending = st.checkbox('Τροποποίηση υπολοίπου;',
                                           key = 'edit_pending')
                new_pending = st.number_input('Νέο υπόλοιπο',
                                              min_value = 0,
                                              max_value = 99,
                                              key = 'new_pending')

                edit_due_date = st.checkbox('Τροποποίηση προθεσμίας',
                                            key = 'edit_due_date')
                new_due_date = st.date_input('Νέα προθεσμία καμπάνιας',
                                             key = 'new_due_date')

                edit_code = st.checkbox('Τροποποίηση κωδικού;',
                                        key = 'edit_code')
                new_code = st.text_input('Νέος Κωδικός',
                                         key = 'new_code').upper()
                new_code = gr_to_en(new_code)

            checkboxes = [edit_section, edit_code, edit_position, edit_quantity,
                          edit_pending, edit_start_date, edit_due_date,
                          edit_trial, edit_crc]

            new_values = [{'section': new_section},
                          {'code': new_code},
                          {'position': new_position},
                          {'quantity': new_quantity},
                          {'pending': new_pending},
                          {'start_date': new_start_date},
                          {'due_date': new_due_date},
                          {'trial': new_trial},
                          {'crc': new_crc}]

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

                        else:
                            batch = db.batch()
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
        clear_state(add_vars + edit_vars + scrap_vars)

        st.header(schedule_page)

        delete_cols0 = st.columns([0.32, 0.68])
        with delete_cols0[0]:
            delete_section = st.selectbox('Εγκατάσταση',
                                          sections,
                                          key = 'delete_section')

        with st.expander('Πίνακας παραγγελιών'):
            delete_empty = st.empty()
            delete_table = orders.query("Εγκατάσταση == '{}'".format(delete_section))\
                .sort_values(by = 'Θέση', ignore_index = True)
            delete_empty.dataframe(delete_table)

        with st.form(key = 'delete_form'):
            delete_cols1 = st.columns([0.32, 0.68])

            with delete_cols1[0]:
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

    elif schedule_page == 'Στοιχεία προϊόντων':
        clear_state(add_vars + edit_vars + delete_vars + scrap_vars)

        st.header(schedule_page)

        with st.expander('Πίνακας προϊόντων'):
            st.dataframe(products_data)

        with st.form(key = 'form_product'):
            prod_cols0 = st.columns([0.32, 0.68])

            with prod_cols0[0]:
                prod_code = st.selectbox('Κωδικός προϊόντος',
                                         products_data['Κωδικός'],
                                         key = 'prod_code')

            if st.form_submit_button('Προβολή επιλογής'):
                st.dataframe(products_data.query("Κωδικός == @prod_code"))

    elif schedule_page == 'Καταχώρηση scrap':
        clear_state(add_vars + edit_vars + delete_vars)

        st.header(schedule_page)

        scrap_cols0 = st.columns([0.32, 0.32, 0.36])

        with scrap_cols0[0]:
            scrap_section = st.selectbox('Εγκατάσταση',
                                          sections,
                                          key = 'scrap_section')

        with scrap_cols0[1]:
            scrap_entry = st.selectbox('Εγγραφή',
                                       range(1,6),
                                       key = 'scrap_entry')

        with st.form(key = 'form_scrap'):
            scrap_cols1 = st.columns([0.32, 0.68])

            with scrap_cols1[0]:
                scrap_text = st.text_input('Νέα καταχώρηση',
                                           key = 'scrap_text')
                st.write('Τρέχουσα καταχώρηση:',
                         scrap.query("section == @scrap_section")[str(scrap_entry)].values[0])

            if st.form_submit_button('Καταχώρηση'):
                batch = db.batch()
                for doc in db.collection('scrap').\
                        where('section', '==', scrap_section).stream():
                            batch.update(doc.reference, {str(scrap_entry): scrap_text})
                batch.commit()

                st.markdown(':white_check_mark: Το είδος scrap καταχωρήθηκε επιτυχώς!')
                st.markdown(':grey_exclamation: Η μεταβολή θα εμφανιστεί \
                                στον πίνακα όταν η σελίδα ανανεωθεί.')

    elif schedule_page == "Παραγγελίες":
        clear_state(add_vars + edit_vars + delete_vars + scrap_vars)

        # st.header(schedule_page)
        display = st.radio('Προβολή', ['Καρτελάκια', 'Πίνακες'], key = 'display')

        if display == 'Πίνακες':
            for section in sections:
                st.markdown('### Εγκατάσταση **{}**'.format(section))
                show_table = orders.query("Εγκατάσταση == '{}'".format(section))\
                    .sort_values(by = 'Θέση', ignore_index = True)
                st.dataframe(show_table)
        else:
            max_cards = 10
            with open('templates/template-cards.html', 'r') as f:
                html_cards = Template(f.read())
            with open('templates/template-scrap.html', 'r') as f:
                html_scrap = Template(f.read())

            former = ['a01', 'a02', 'a03', 'a04', 'a05', 'a06', 'a07', 'a08', 'a09', 'a10']
            mapping = {i + j[1:] : '' for i in former for j in former + ['a11', 'a12', 'a13']}
            style = {'0': 'card', '1': 'trial'}
            mappings = {section: {**mapping} for section in sections}
            scrap_cards = {}

            for i in range(1, max_cards + 1):
                for section in sections:
                    section_data = orders.query("Εγκατάσταση == @section")\
                        .sort_values(by = 'Θέση', ignore_index = True)
                    if i <= section_data.shape[0]:
                        try:
                            code = section_data.loc[i-1, 'Κωδικός']
                            code = gr_to_en(code)
                            prod_id = products_data.query("Κωδικός == @code").index.values[0]

                            mappings[section][former[i-1] + '01'] = code
                            mappings[section][former[i-1] + '02'] = products_data.loc[prod_id, 'Πελάτης']
                            mappings[section][former[i-1] + '03'] = products_data.loc[prod_id, 'Διαστάσεις']
                            mappings[section][former[i-1] + '04'] = products_data.loc[prod_id, 'Κράμα']
                            mappings[section][former[i-1] + '05'] = products_data.loc[prod_id, 'Επεξεργασία']
                            mappings[section][former[i-1] + '06'] = int(products_data.loc[prod_id, 'Πλήθος'])
                            mappings[section][former[i-1] + '07'] = int(products_data.loc[prod_id, 'Μήκος'])
                            mappings[section][former[i-1] + '08'] = products_data.loc[prod_id, 'Ανοχές']
                            mappings[section][former[i-1] + '09'] = products_data.loc[prod_id, 'Βάρος']
                            mappings[section][former[i-1] + '10'] = section_data.loc[i-1, 'Πλήθος'] - section_data.loc[i-1, 'Υπόλοιπο']
                            mappings[section][former[i-1] + '11'] = '/ ' + str(section_data.loc[i-1, 'Πλήθος'])
                            mappings[section][former[i-1] + '12'] = style[str(int(section_data.loc[i-1, 'Δοκιμή']))]

                            if section != 'Β':
                                slab_width = products_data.loc[prod_id, 'Διαστάσεις'].split('x')[1]

                                if section_data.loc[i-1, 'CRC'] != 'N/A':
                                    chosen_box = section_data.loc[i-1, 'CRC']
                                else:
                                    chosen_box = 'text'
                                    for box in crc.loc[slab_width, 'Κουτιά']:
                                        if box in crc_unique:
                                            chosen_box = box
                                            break
                                        if chosen_box == 'text':
                                            chosen_box = crc.loc[slab_width, 'Κουτιά'][0]

                                try:
                                    crc_unique.remove(chosen_box)
                                    mappings[section][former[i-1] + '13'] = chosen_box
                                except KeyError:
                                    mappings[section][former[i-1] + '13'] = '<span style="color:#CD6123">' + chosen_box + '</span>'

                        except:
                            mappings[section][former[i-1] + '01'] = code
                            mappings[section][former[i-1] + '02'] = 'Άγνωστο Προϊόν'
                            mappings[section][former[i-1] + '10'] = section_data.loc[i-1, 'Υπόλοιπο']
                            mappings[section][former[i-1] + '11'] = '/ ' + str(section_data.loc[i-1, 'Πλήθος'])
                            mappings[section][former[i-1] + '12'] = style[str(int(section_data.loc[i-1, 'Δοκιμή']))]
                    else:
                        pass

            for section in sections:
                scrap_data = scrap.query("section == @section")
                scrap_card = html_scrap.safe_substitute(a1 = section,
                                                        a2 = scrap_data["1"].values[0],
                                                        a3 = scrap_data["2"].values[0],
                                                        a4 = scrap_data["3"].values[0],
                                                        a5 = scrap_data["4"].values[0],
                                                        a6 = scrap_data["5"].values[0])

                scrap_cards[section] = scrap_card

                card_cols = st.columns([0.12, 0.88])

                with card_cols[0]:
                    st.components.v1.html(scrap_cards[section],
                                          height = 260,
                                          scrolling = False)

                with card_cols[1]:
                    card = html_cards.safe_substitute(**mappings[section])
                    st.components.v1.html(card, height = 260, scrolling = True)

streamlit_analytics.stop_tracking()
