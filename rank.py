'''
Purpose: Implement a rank choice voting scheme.
'''

import streamlit as st
import polars as pl
import pygsheets

def main():
    '''Launch a streamlit page to track and vote on books for book club'''
    current = getNominees()

    # Create an option for each book to vote on
    options = [item + 1 for item in range(len(current))]
    with st.form('rankChoice'):
        vote = {}
        # List out all of the book options
        for n in range(len(current)):
            book = current['book'][n]
            vote[book] = st.selectbox(book, options = options)

        st.form_submit_button('Vote!')
    
    # Check that the votes were cast correctly
    cast = []
    for item in vote:
        result = vote[item]
        if result not in cast:
            cast.append(result)
        else: 
            st.error("You have multiple books with the same ranking!")
            return

    # Print out the results
    st.write(vote)

@st.cache_resource(ttl = 300)
def getNominees():
    # Establish connection
    sheet = connection()

    # Read the current nominees
    df, sheetNum = sheet.getBooks()

    # Get the list of current nominees
    current = df.filter(
        # We want to see books that are currently nominated
        pl.col('nominated') == 'TRUE',

        # We don't want books that are currently nominated
        pl.col('victorious') == ''
    )

    return current

@st.cache_resource(ttl = 3600)
def connection():
    '''Establish the connection and return the sheet'''
    # JSON file with the sheet connection details
    file = r'glassy-mystery-427419-e0-a8061269c27e.json'
    
    # Create the connection
    sheet = sheets(file)

    return sheet

class sheets:
    '''Class to read and write from the Book Club spreadsheet'''

    def __init__(self, jsonFile):
        '''Establish Connection'''

        # Set up the sheets connection
        self.gc = pygsheets.authorize(service_file = jsonFile)

        # Connect to the Book Club Database
        self.sh = self.gc.open('Book Club Database')

    def getBooks(self):
        '''Reads the current list of nominees from the database'''
        # Find the "Suggested Books" sheet
        n = 0
        while True:
            if self.sh[n].title == 'Suggested Books':
                break
            n += 1

        # Read in the sheet and convert to dataframe
        df = pl.from_pandas(self.sh[n].get_as_df())

        # Return the dataframe
        return df, n

    def resetNominees(self):
        '''Resets the nominee field to be false for all books'''
        # Read in the current dataframe
        df, n = self.getBooks()

        # Reset all 'nominated' fields to False
        df = df.with_columns(pl.col('nominated').map_elements(lambda x: False, return_dtype = pl.Boolean))

        # Rewrite the data on the sheet
        self.sh[n].set_dataframe(df.to_pandas(), (1,1))

    def votingPage(self):
        '''Creates a streamlit page to vote on books'''
        
if __name__ == '__main__':
    main()