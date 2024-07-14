'''
Purpose: This page will allow users to track and nominate books
        to vote on.

Author: Nick Xydis
Date: 01Jul2024
'''

import streamlit as st
import polars as pl
import datetime

# Dashboard helper
import dashboardHelper as h

def main():
    # Set up the google sheet
    sheet = st.session_state['sheet']

    # Read in the current book list
    df, sheetNum = sheet.getBooks()

    # Columns
    col1, col2 = st.columns(2)

    # Get the list of current nominees
    current = df.filter(
        # We want to see books that are currently nominated
        pl.col('nominated') == 'TRUE',

        # We don't want books that are currently nominated
        pl.col('victorious') == ''
    )

    # Store the current nominees in the session state
    st.session_state['currentNominees'] = current

    # Button to reset the nominee list
    with col1:
        st.button('Reset Nominees', on_click = reset)

    # Button to initiate an election
    with col2:
        st.button('Start Election', on_click = startElection)

    # Display the current nominees
    st.write("# Current nominees")
    unnomEvent = st.dataframe(current, 
                on_select = 'rerun',
                selection_mode = 'single-row', 
                hide_index = True)
    
    # If we selected something to be unnominated, unnominate it
    unnom = unnomEvent.selection['rows']
    if len(unnom):
        # Index of the unnominated book
        n = unnom[0]

        # Get the book title of the unnominated book
        book = current['book'][n]

        # Get the row of the book that was just selected
        row = df.with_row_index().filter(pl.col('book') == book)['index'][0]

        # Update the value
        df[row, 'nominated'] = False

        # Write the data
        sheet.sh[sheetNum].set_dataframe(df.to_pandas(), (1, 1))

        # Reset the page to reflect the changes
        st.rerun()

    # Get the non-nominated book list
    unnominated = df.filter(
        # We want to see books that are not currently nominated
        pl.col('nominated') == 'FALSE',

        # We also don't want to look at books that have already been picked
        pl.col('victorious') == ''
    )
    
    # Display the results
    st.write('# Nominate a book')
    nomEvent = st.dataframe(unnominated, 
                on_select = 'rerun',
                selection_mode = 'single-row', 
                hide_index = True)

    # If we have something selected, nominate it
    if len(nomEvent.selection['rows']):
        n = nomEvent.selection['rows'][0]
        
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
    '''Resets the value for current nominees and vote status'''
    sheet = st.session_state['sheet']
    sheet.resetNominees()

def startElection():
    '''Starts an election with the current nominees as the candidates'''
    # Shorthand to get the current nominees
    current = st.session_state['currentNominees']

    # Today's date
    today = datetime.datetime.today()
    today = today.strftime('%d%b%Y')

    # Make a temporary dataframe
    temp = current.with_columns(
        pl.col('book').map_elements(lambda x: today, return_dtype = pl.Utf8).alias('election_date')
    )
    temp = temp[['book', 'election_date']]

    # Current sheet
    sheet = st.session_state['sheet']

    # Get the election sheet number
    n = 0
    while True:
        name = sheet.sh[n].title
        if name == 'Election':
            break

        # Increment
        n += 1

    # Store the election sheet
    election = sheet.sh[n]

    # Read in the current data
    df = pl.from_pandas(election.get_as_df())

    # Add the new data
    df = pl.concat([df, temp], how = 'diagonal_relaxed')

    # Write the data back
    election.set_dataframe(df.to_pandas(), (1, 1))

    # If success... party time
    st.snow()

    # Reset the current nominees
    reset()

if __name__ == '__main__':
    h.initAll()
    main()