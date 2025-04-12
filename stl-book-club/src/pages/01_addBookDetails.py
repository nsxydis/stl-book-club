'''
Purpose: Add a book to the database.
'''
# Standard modules
import streamlit as st
import requests

# Import helper
import dashboardHelper as dh

# Key Import options
try:
    from key import apiKey, apiFile
except:
    apiKey = st.secrets['apiKey']
    # json = str(st.secrets['json']).replace("'", '"')

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

            # Add the details to the session state & cached details
            book = keys[n]
            details = info[keys[n]]
            st.session_state['details'][book] = details

            # Display message
            st.toast(f'Added: {book}')

            # Add the book to the voting list (if it's not there already)
            if book not in st.session_state['books']:
                st.session_state['books'].append(book)



class bookSummary:
    '''Pulls and writes the book summaries'''
    
    def __init__(self):
        self.apiKey = apiKey

    def get_book_info(self, title):
        # Define the endpoint
        endpoint = "https://www.googleapis.com/books/v1/volumes"

        # Set up the parameters
        params = {
            'q': title,  # Query with the book title
            'key': apiKey,  # Replace with your Google Books API key
            'country'   : 'US'
        }

        # Make the request to the API
        response = requests.get(endpoint, params=params)

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            
            # Check if there are any books in the response
            if 'items' in data:

                # Set up a dataframe
                books = {}

                # Loop through all the results
                for book in data['items']:

                    # Get the book info for the book in question
                    bookInfo = book['volumeInfo']

                    # Get all the book information and add it to the dictionary
                    b = bookInfo.get('title')

                    # Check if the book has been added before
                    n = 1
                    while True:
                        # Exit if we have something we haven't seen before
                        if b not in books:
                            break

                        # Otherwise reprocess the information
                        else:
                            # Remove the end numbers if we've added them
                            if n >= 10:
                                b = b[:-3]
                            elif n > 1:
                                b = b[:-2]

                            # Increment
                            n += 1

                            # Rename
                            b = f'{b}_{n}'

                    # Get the authors and convert to a string
                    authors = bookInfo.get('authors')
                    if authors:
                        authors = ', '.join(author for author in authors)

                    books[b] = {
                        'id'            : book.get('id'),
                        'author'        : authors,
                        'pages'         : bookInfo.get('pageCount'),
                        'avgRating'     : bookInfo.get('averageRating'),
                        'ratingCount'   : bookInfo.get('ratingsCount'),
                        'description'   : bookInfo.get('description')
                    }

                    try:
                        imageLinks = bookInfo.get('imageLinks')
                        books[b]['image'] = imageLinks.get('thumbnail')
                    except:
                        books[b]['image'] = None

                return books
            else:
                return 'No books found for the given title.', None
        else:
            return f'Error: {response.status_code}', None

    def apiDisplayBookInfo(self, book, bookInfo):
        '''Displays the book information from the API in a more organized format'''
        # Display the book title
        st.write(f'# {book}')

        # Make the columns
        col1, col2, col3 = st.columns([0.25, 0.25, 0.5])

        # Display the image, if there is one
        image = bookInfo['image']
        if image:
            with col1:
                st.image(image)

        # Display the book stats
        with col2:
            # Write the authors
            st.write('##### By:')
            st.write(bookInfo['author'])

            # Write the number of pages
            st.write('##### Pages:')
            st.write(bookInfo['pages'])

            # Write the average Rating
            st.write('##### Average Rating:')
            st.write(bookInfo['avgRating'])

            # Write the number of ratings
            st.write('##### Number of ratings:')
            st.write(bookInfo['ratingCount'])

        # Write the description of the book
        with col3:
            st.write('### Description:')
            st.write(bookInfo['description'])
      
if __name__ == '__main__' or True:
    dh.initAll()
    main()