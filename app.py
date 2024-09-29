'''
Streamlit app
'''
import streamlit as st
pages = [
        st.Page('pages/00_instructions.py', title = 'Instructions', default = True),
        st.Page('rank.py', title = 'Vote'),
        st.Page('pages/01_addBookDetails.py', title = 'Add Book'),
        st.Page('pages/02_updateBookDetails.py', title = 'Modify Book')
    ]
nav = st.navigation(pages)
nav.run()