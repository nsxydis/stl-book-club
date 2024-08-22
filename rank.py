'''
Purpose: Simple voting app to implement ranked choice voting.
'''

import streamlit as st
import polars as pl
import altair as alt

# Defaults
st.session_state['debug'] = False

def main():
    # Init books
    books, votes = init()

    col1, col2 = st.columns(2)

    with col1:
        # Refresh button
        refresh = st.button('Refresh Page')
        if refresh:
            st.rerun()

    with col2:          
        # Add a button to clear the cache
        clear = st.button("Reset Books & Votes")
        if clear:
            # Set the default confirmation response to False
            if 'yes' in st.session_state:
                st.session_state['yes'] = False
            st.warning("Are you sure?")
            st.button("Heck yes", key = 'yes')
            st.button("No")

        # If we have an answer and the answer for yes == True, reset the cache
        if 'yes' in st.session_state and st.session_state['yes'] == True:
            # Clear cache
            st.cache_resource.clear()
            st.rerun()

    # Set the value of book equal to the input data
    if 'book' in st.session_state:
        book = st.session_state['book'].strip()
        st.session_state['book'] = ''
    else:
        book = ''

    # Add a book -- removing whitespace
    st.text_input("Add a book to the voting arena", key = 'book').strip()
    if book:
        # Add the result if it's not in our data already
        if book not in books:
            books.append(book)
            st.success(f"Added book: {book}")

    # Sort the books, because we're not heathens
    books.sort()
    
    # Remove a book -- removing whitespace
    with st.form("remove book"):
        remove = st.selectbox('Remove a book from the voting arena', options = books)
        removeBook = st.form_submit_button("Remove Book")
    
    # If we submitted a book to be removed, remove it
    if removeBook:
        if remove in books:
            st.warning(f'Removing book: {remove}')
            books.remove(remove)
            st.rerun()
    
    # Debug: Check the current books list and what's been added or removed
    if st.session_state['debug']:
        st.write("TEMP")
        st.write(books)
        st.write(f'Added book: {book}')
        st.write(f'Removed book: {remove}')

    # Get the number of books, and thus number of categories
    n_books = len(books)

    # currentVote init
    currentVote = {}

    # Voting form
    with st.form('Voting Page'):
        # Instructions
        st.write('## Instructions:')
        st.write('1) Rank your preference of each book. 1 is the most preferred choice, 2 is the second...')
        st.write('2) If you do not want to vote for a book, give it a Rank value of 0 (the default).')
        st.write('3) You cannot give the same Ranking to multiple books. All Ranks must be unique or 0.')
        st.write('4) Please only vote once!')
        
        # Display the current list of books
        for book in books:
            # Insert a line separator
            st.markdown('---')

            col1, col2, col3 = st.columns(3)
            
            # Display the book we're voting on
            with col1:
                st.write(f'### {book}')

            # Voting categories
            with col2:
                currentVote[book] = st.number_input(f'{book} Rank', min_value = 0, max_value = n_books)

        st.markdown('---')
        vote = st.form_submit_button("Submit Vote!")

    # Check the vote meets our criteria
    if vote:
        values = []
        for key, value in currentVote.items():
            if value > 0:
                if value not in values:
                    values.append(value)
                else:
                    st.error("One or more of your votes have the same ranking")
                    return

        # If all is good, update the vote status
        st.session_state['voted'] = True
        st.write("## Your Vote:")
        st.write(currentVote)
        votes.append(currentVote)

    # Display the current number of votes
    st.write(f"# Number of Votes: {len(votes)}")
    st.write('Use the "Refresh" button or refresh the page to see the results as they come in.')
    st.write('NOTE: When you refresh the page, the vote you casted will no longer be displayed.')

    # Convert the votes to a dataframe
    data = {
        'name'  : [],
        'book'  : [],
        'rank'  : []
    }

    n = 0
    for vote in votes:
        n += 1
        user = f'user_{n}'
        for  key, value in vote.items():
            # Skip 0 votes
            if value == 0:
                continue
            data['name'].append(user)
            data['book'].append(key)
            data['rank'].append(value)

    df = pl.DataFrame(data)

    # If we don't have data, don't score
    if len(df) == 0:
        return
    
    # Otherwise run the voting algo
    rankChoice(df)


@st.cache_resource()
def init():
    '''Initializes global variables'''
    books = []
    votes = []
    return books, votes

### Copied functions
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
        st.write(f"## {highest['book'][0]}!!!")
    
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
                st.write(f"## {highest['book'][0]}!")
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
    main()