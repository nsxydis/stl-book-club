'''
Purpose: View information about a book title.
'''
import streamlit as st
import requests
from key import apiKey

def main():
    # Example usage
    book_title = "The Three Body Problem"
    book_info, cover_image = get_book_info(book_title)
    st.write(book_info)
    st.image(cover_image)
    

def get_book_info(title):
    # Define the endpoint
    endpoint = "https://www.googleapis.com/books/v1/volumes"

    # Set up the parameters
    params = {
        'q': title,  # Query with the book title
        'key': apiKey,  # Replace with your Google Books API key
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
            images = []

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

                books[b] = {
                    'id'            : book.get('id'),
                    'author'        : bookInfo.get('authors'),
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

if __name__ == '__main__':
    main()