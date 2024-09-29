'''
Purpose: Instructions for using the dashboard.
'''

import streamlit as st
import dashboardHelper as dh

def main():
    st.title("How to use this dashboard")

    st.write("# Adding a book")
    text = '''If you would like to add a book to be voted on, you have a couple of options:
    
    1. You can manually enter the book title on the "Vote" page
    2. You can search for the book in the "Add Book" page

If you add a book via option 1, then the book won't have any details like author,
page count, etc.... If you add a book via option 2, it's possible the information
may not be entirely accurate. To change the details of a book, go to the
Modify Book Details tab.
    '''
    st.write(text)

    st.info('''If you want to change book details, they need to exist first.
    You can add details for a book even if it was added manually -- the titles just need to match.''')

    # Voting information
    st.write('# Voting')
    
    # Instructions
    text = '''
    1. Rank your preference of each book. 1 is the most preferred choice, 2 is the second....
    2. If you do not want to vote for a book, give it a Rank value of 0 (the default).
    3. You cannot give the same Ranking to multiple books. All Ranks must be unique or 0.
    4. Please only vote once!
'''    

if __name__ == '__main__' or True:
    dh.initAll()
    main()