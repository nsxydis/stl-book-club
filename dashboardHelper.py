'''
Setup some of the functions for the dashboard.
'''
import streamlit as st
ss = st.session_state

def initAll():
    books, votes, details = data()
    init('books', books)
    init('votes', votes)
    init('details', details)
    pageNavigation()

def init(variable, value = None):
    '''Initializes something in the session state if it is not already there'''
    if variable not in ss:
        ss[variable] = value

@st.cache_resource()
def data():
    '''Initializes global variables'''
    books = []      # List of the current books to vote on
    votes = []      # List of the current votes
    details = {}    # Dictionary of the stored book details

    return books, votes, details

def pageNavigation():
    '''Define navigation for the application'''
    pages = [
        st.Page('pages/00_instructions.py', title = 'Instructions', default = True),
        st.Page('rank.py', title = 'Vote'),
        st.Page('pages/01_addBookDetails.py', title = 'Add Book'),
        st.Page('pages/02_updateBookDetails.py', title = 'Modify Book Details')
    ]
    nav = st.navigation(pages)
    nav.run()