'''
Purpose: This page will allow users to track and nominate books
        to vote on.

Author: Nick Xydis
Date: 01Jul2024
'''

import streamlit as st
import polars as pl
from rank import connection


def main():
    # Set up the google sheet
    sheet = connection()

    # Read in the current book list
    df, sheetNum = sheet.getBooks()

    # Button to reset the nominee list
    st.button('Reset Nominees', on_click = reset)

    # Get the list of current nominees
    current = df.filter(
        # We want to see books that are currently nominated
        pl.col('nominated') == 'TRUE',

        # We don't want books that are currently nominated
        pl.col('victorious') == ''
    )

    # Display the current nominees
    st.write("# Current nominees")
    st.dataframe(current, hide_index = True)

    # Get the non-nominated book list
    unnominated = df.filter(
        # We want to see books that are not currently nominated
        pl.col('nominated') == 'FALSE',

        # We also don't want to look at books that have already been picked
        pl.col('victorious') == ''
    )
    
    # Display the results
    st.write('# Nominate a book')
    event = st.dataframe(unnominated, 
                on_select = 'rerun',
                selection_mode = 'single-row', 
                hide_index = True)

    # If we have something selected, nominate it
    if len(event.selection['rows']):
        n = event.selection['rows'][0]
        
        # Get the name of the book that was selected
        book = unnominated['book'][n]

        # Get the row of the book that was just selected
        row = df.with_row_index().filter(pl.col('book') == book)['index'][0]

        # Update the value
        df[row, 'nominated'] = True

        # Write the data
        sheet.sh[sheetNum].set_dataframe(df.to_pandas(), (1,1))  

        # Reset the page
        st.rerun()

def reset():
    '''Resets the value for current nominees'''
    sheet = connection()
    sheet.resetNominees()

if __name__ == '__main__':
    main()