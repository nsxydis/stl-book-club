'''
Purpose: Add a book to the database.
'''

import streamlit as st
from dashboardHelper import bookSummary, initAll

def main():
    # Look up book info
    title = st.text_input('Search for a book')
    if title == '':
        return
    
    b = bookSummary()
    info = b.get_book_info(title)

    # Check that we got a result...
    if info == 'No books found for the given title.':
        st.write("No data found for this book!")
        show = False

    # Check if there was an error...
    elif type(info) == str and info.startswith('Error'):
        st.write("An error has occurred:")
        st.write(info)
        return
    
    # Otherwise, display the results...
    else:
        show = True
    
    # If we did get a result, display the results
    if show:
        # Init
        st.session_state['numBooks'] = 0

        # Session State
        st.session_state['b'] = b
        st.session_state['info'] = info

        # TEMP
        st.write(info)

        for book in info:
            # Display the book information
            b.apiDisplayBookInfo(book, info[book])

            # Make a button to select this book
            st.button(f'Select {book}', key = f'addBook_{st.session_state['numBooks']}', on_click = addNewBook)
            st.markdown('---')

            # Increment
            st.session_state['numBooks'] += 1

def addNewBook():
    '''Adds the given book information to the database'''
    # Shorthand
    b = st.session_state['b']
    info = st.session_state['info']

    # Loop through all the book options
    for n in range(st.session_state['numBooks']):
        item = f'addBook_{n}'
        if st.session_state[item]:
            # Figure out which book it was
            keys = list(info.keys())
            b.writeBookInfo(keys[n], info[keys[n]])

if __name__ == '__main__':
    initAll()
    main()
    
    # Remove excess data from the session state
    if 'info' in st.session_state: st.session_state.pop('info')