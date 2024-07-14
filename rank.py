'''
Purpose: Implement a rank choice voting scheme.
'''

# Standard modules
import streamlit as st
import polars as pl
import altair as alt

# Custom Modules
import dashboardHelper as h     # Helper for the dashboard

def main():
    '''Launch a streamlit page to track and vote on books for book club'''
    # current = getNominees()

    # Check if the user has voted already
    v = h.vote()

    # Basic check to see if we should continue
    try:
        _ = v.name
    except:
        return
    
    # Get the current nominees
    current = v.currentElection()

    # Display the current results
    if v.checkVote():
        # Pull the data
        df = pl.from_pandas(
            v.voteSheet.get_as_df()
        )

        # Filter for the votes casted today
        df = df.filter(
            pl.col('vote_date') == v.user.date
        )

        # Rank choice voting
        rankChoice(df)

        # Stop the page generation
        return

    # Create an option for each book to vote on
    options = [item + 1 for item in range(len(current))]

    # Add an option to not vote for something
    options.append('N/A')

    # Voting form
    with st.form('rankChoice'):
        userVote = {}
        # List out all of the book options
        for n in range(len(current)):
            book = current['book'][n]
            userVote[book] = st.selectbox(book, options = options)

        st.form_submit_button('Vote!')
    
    # Check that the votes were cast correctly
    cast = []
    for item in userVote:
        result = userVote[item]
        if result not in cast:
            try: 
                cast.append(int(result))
            except:
                pass
        else: 
            st.error("You have multiple books with the same ranking!")
            return
        
    # Save the vote
    v.vote(userVote)

    # Refresh the page
    st.rerun()

def getNominees():
    '''Get the nominees'''
    # Establish connection
    sheet = st.session_state['sheet']

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

def rankChoice(df, round = 1, scale = None):
    '''Run the ranked choice algorithm'''
    # Keep track of the rounds
    results = {}

    # Find the highest ranked vote for each person
    for name in df['name'].unique().to_list():
        subset = df.filter(pl.col('name') == name)
        lowestRank = float('inf')
        book = None

        # Just look at the results for that person
        for n in range(len(subset)):
            rank = subset['rank'][n]

            # The lower a rank value is, the higher the value of the choice
            if rank != None and rank < lowestRank:
                lowestRank = rank
                book = subset['book'][n]

        
        # If we got a book, add it to our results
        if book:
            if book not in results:
                results[book] = 1
            else:
                results[book] += 1

    # Convert the results to a dataframe
    r = {
        'book'  : [],
        'votes' : []
    }
    for book in results:
        r['book'].append(book)
        r['votes'].append(results[book])

    # Add any books that didn't get votes back in
    for book in df['book'].unique().to_list():
        if book not in r['book']:
            r['book'].append(book)
            r['votes'].append(0)

    # Convert the round results to a dataframe
    r = pl.DataFrame(r)

    # Add the percentage to the dataframe
    r = r.with_columns(
        (pl.col('votes') / r['votes'].sum()).alias('percent')
    )

    # Sort the results by vote
    r = r.sort(by = 'votes', descending = True)

    # Set the scale
    if scale == None:
        scale = alt.Scale(domain = sorted(r['book'].unique().to_list()))

    # Plot the results
    chart = alt.Chart(r.to_pandas()).mark_bar().encode(
        x = 'book',
        y = 'votes',
        color = alt.Color('book', scale = scale),
        tooltip = [
            'book',
            'votes',
            alt.Tooltip('percent', format = '.1%')
        ]
    )
    chart.title = f'Round {round} results'

    # Show the chart
    st.altair_chart(chart)

    # Check if the top result got more than 50% of the vote
    top = r['votes'].max() / r['votes'].sum()
    
    # If the top result has more than 50% of the vote, we have a winner
    if top > .5:
        highest = r.filter(pl.col('votes') == r['votes'].max())
        st.write("# The winning book is:")
        st.write(f'## {highest['book'][0]}!!!')
    
    else:
        # Endless loop catch
        if round > 100:
            st.error("More than 100 rounds have passed without a victor...")
            return
        
        # Get the lowest result(s)
        lowest = r.filter(pl.col('votes') == r['votes'].min())
        lowestBooks = lowest['book'].unique().to_list()

        # Remove the results (the one's that don't have the lowest votes)
        dfUpdate = df.filter(pl.col('book').is_in(lowestBooks) == False)

        # If the new dataframe has a length of 0, we have an issue
        if len(dfUpdate) == 0:
            # Warn the user
            st.warning("No clear winner, trying a tie break")

            # Try to sum the rank of each remaining candidate
            dfUpdate = df.group_by('book').agg(pl.col('rank').mean())

            # We want to find the item that has the lowest average rank score
            highest = dfUpdate.filter(
                pl.col('rank') == dfUpdate['rank'].min()
            )

            # If we have a winner now...
            if len(highest) == 1:
                st.write('# The winning book is:')
                st.write(f'## {highest['book'][0]}!')
                return
            
            # If there still isn't a winner, randomly select between the options
            st.error('The tie break method did not work...')
            import random

            # Combine the remaining books into a single string
            string = ''
            books = sorted(dfUpdate['book'].unique().to_list())
            for item in books:
                string += item

            # Convert the string to a number
            randomSeed = string_to_int_custom(string)

            # Use this as the random seed
            random.seed(randomSeed)

            # Randomly select one of the remaining books
            book = books[random.randint(0, len(books) - 1)]

            st.write("# Randomly selected from the remaining books...")
            st.write(f'## {book} is the winner!')
            return

        # Run the algorithm again
        rankChoice(dfUpdate, round + 1, scale)

def string_to_int_custom(s):
    # Create a mapping of each character to a unique number
    char_to_num = {char: idx for idx, char in enumerate(sorted(set(s)))}
    # Convert the string to a number based on the mapping
    num = 0
    for char in s:
        num = num * 100 + char_to_num[char]  # Use a base large enough to avoid collisions
    return num
        
if __name__ == '__main__':
    h.initAll()
    main()