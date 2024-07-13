'''
Purpose: Add a book to the database.
'''

import streamlit as st
from rank import connection
import polars as pl
# import bookSummary
import datetime
from classes import bookSummary

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

        for book in info:
            # Display the book information
            b.apiDisplayBookInfo(book, info[book])

            # Make a button to select this book
            st.button(f'Select {book}', key = f'addBook_{st.session_state['numBooks']}', on_click = addNewBook(b, info))
            st.markdown('---')

            # # Make a heading for the book we're looking at
            # st.write(f"# {book}")

            # # Get the image, if there is one
            # image = info[book].pop('image')

            # # If we got a picture, display it
            # if image:
            #     st.image(image)

            # # Show the book information
            # st.write(info[book])

            # # Add the image info back
            # info[book]['image'] = image

            # Increment
            st.session_state['numBooks'] += 1

def addNewBook(b, info):
    '''Adds the given book information to the database'''
    for n in range(st.session_state['numBooks']):
        item = f'addBook_{n}'
        if st.session_state[item]:
            # Figure out which book it was
            keys = list(info.keys())
            b.writeBookInfo(keys[n], info[keys[n]])
            
            # checkBook(info[keys[n]], keys[n])

            # Reset the key so we don't do this again
            st.session_state[item] = False

def checkBook(bookInfo, book):
    '''Checks if the given book information is in our database already
    and if not, will add the data'''
    # Establish connection
    sheet = connection()

    # Read in the data
    df, n = sheet.getBooks()

    # Check if our title is in the database already
    check = df.filter(pl.col('book') == book)

    # If we didn't find anything, then add the new book
    if len(check) == 0:
        today = datetime.datetime.today()
        data = {
            'book'              : book,
            'id'                : bookInfo['id'],
            'date_suggested'	: today.strftime('%d%b%Y'),
            'times_voted_on'	: 0,
            'nominated'	        : 'FALSE',
            'victorious'	    : '',
            'Rating'            : ''
        }

        # Create the dataframe
        data = pl.DataFrame(data)

        # Add the new data to the old data
        df = pl.concat([df, data], how = 'diagonal_relaxed')

        # Add the book
        sheet.sh[n].set_dataframe(df.to_pandas(), (1,1))

    


    
if __name__ == '__main__':
    main()