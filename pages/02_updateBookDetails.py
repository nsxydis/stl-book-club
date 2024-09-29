'''
Purpose: Allow the user to update some of the book details in case they are not accurate.
'''
import streamlit as st
import dashboardHelper as dh

def main():
    st.title("Modify Stored Book details")
    
    # Loop through all the books to change
    n = 0
    for key, value in st.session_state['details'].items():
        with st.form(f'update {key}'):
            # Show the book title
            st.write(f'## {key}')
            st.session_state[f'book_{n}'] = key

            # Title
            st.text_input('Title', value = key, key = f'title_{n}')

            # Author
            st.text_input('Author', value = value['author'], key = f'author_{n}')
            
            # Pages
            st.number_input('Number of Pages', value = value['pages'], key = f'pages_{n}')
            
            # Description
            st.text_area('Description', value = value['description'], key = f'description_{n}')

            # Change details button
            st.form_submit_button(f'Change {key} details', on_click=submit)

            # Increment
            n += 1

def submit():
    '''On change, submit changes to the session state'''
    # Shorthand
    details = st.session_state['details']
    ss = st.session_state

    # Loop
    n = 0
    while True:
        # Check that we have a book to update
        if f'book_{n}' not in st.session_state:
            break

        # Check if the title needs to be updated
        if ss[f'book_{n}'] != ss[f'title_{n}']:
            details[ss[f'title_{n}']] = details.pop(ss[f'book_{n}'])

        # Get the title of the book
        title = details[ss[f'book_{n}']]

        # Update the author
        title['author'] = ss[f'author_{n}']

        # Update the page count
        title['pages'] = ss[f'pages_{n}']

        # Update the description
        title['description'] = ss[f'description_{n}']

        # Increment
        n += 1

if __name__ == '__main__' or True:
    dh.initAll()
    main()