'''
Purpose: Helpful functions and classes for the dashboard.
'''
import streamlit as st
import st_pages
from streamlit_cookies_controller import CookieController
import polars as pl
import datetime
import requests
import pygsheets

# Import options
try:
    from key import apiKey, apiFile
except:
    apiKey = st.secrets['apiKey']
    json = str(st.secrets['json']).replace("'", '"')

def main():
    pass

def cookie_main():
    # Set up the cookie class
    user = cookie()
    if user == None:
        st.rerun()

    # Add the user to the log if they're not there already
    user.cookieLog()

    # Vote button
    user.voteButton()

    # Reset button
    user.resetButton()

    # Display the current info
    df = pl.from_pandas(user.workSheet.get_as_df())
    st.dataframe(df)

# Shorthand
ss = st.session_state

def init(name, value):
    '''Checks if the given name is in the session state.
    If not, adds the specified value'''
    if name not in ss:
        ss[name] = value

def initAll():
    '''Initializes all key values for the session state'''
    # Set up the page names
    st_pages.show_pages(
        [
            st_pages.Page('rank.py', 'Homepage'),
            st_pages.Page('pages/addBook.py', 'Search for new books'),
            st_pages.Page('pages/nominate.py', 'Nominate books')
        ]
    )
    # Store the google sheet in the session state
    init('sheet', connection())

@st.cache_data(ttl = 3600)
def connection():
    '''Establish the connection and return the sheet'''
    try:
        # JSON file with the sheet connection details
        file = apiFile
        
        # Create the connection
        sheet = sheets(file)
    except:
        # If we're running on the cloud, use the secrets instead
        sheet = sheets(json = json)

    return sheet

class sheets:
    '''Class to read and write from the Book Club spreadsheet'''

    def __init__(self, jsonFile: 'str' = None, json: 'str' = None):
        '''Establish Connection'''

        # Set up the sheets connection
        if jsonFile:
            self.gc = pygsheets.authorize(service_file = jsonFile)
        elif json:
            self.gc = pygsheets.authorize(service_account_json = json)

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

class cookie:
    '''Cookie Class to store and update user info'''

    def __init__(self):
        '''Set up the cookie infromation for the user'''
         # Get today's date and convert to ddMMMyyy
        today = datetime.datetime.today()
        self.date = today.strftime('%d%b%Y')

        # Establish connection
        self.sheet = connection()

        # Get the sheetNum variable
        self.cookieSheet()

        # Save the workSheet for the Cookie Log
        self.workSheet = self.sheet.sh[self.sheetNum]

        # Get the length of the User Log

        # Set up the cookie for this user
        controller = CookieController()

        # Get all cookies
        cookies = controller.getAll()

        # If the user doesn't have a cookie...
        userID = controller.get('user_cookie')
        if userID:
            self.cookieID = userID
        else:
            # Set a cookie
            userID = len(self.workSheet.get_as_df())
            controller.set('user_cookie', userID)
            self.cookieID = userID

        # try:
        #     # Set the cookie ID for this user
        #     self.cookieID = cookies['user_cookie']
        # except:
        #     self.cookieID = None
        #     # TEMP
        #     st.write('# Cookie')
        #     st.write(cookies)

        if self.cookieID:        
            # Write to the cookie log
            self.cookieLog()

    def cookieSheet(self):
        '''Returns the sheet number with the cookie log'''
        # Figure out which sheet is the cookie log
        n = 0
        while True:
            name = self.sheet.sh[n].title 
            if name == 'User Log':
                break
            n += 1

        # Save the data
        self.sheetNum = n

    def cookieLog(self):
        '''Get, check, and write to the cookie log'''
        # Pull the cookie log
        log = pl.from_pandas(self.workSheet.get_as_df())

        # Check if our cookie is on there already
        check = log.filter(pl.col('cookie') == self.cookieID)
        
        # If not, ask the user who they are and then add their info
        if len(check) == 0:
            st.write("# Welcome!")
            with st.form('Name Entry:'):
                name = st.text_input('Enter Name:')
                st.form_submit_button("Submit")
            
            # If we didn't get a name, ask for one
            if name == '':
                st.error("Please enter a name!")
                return
            else:
                st.session_state['cookieSubmit'] = True
            
            # Make the dataframe to add to our log
            data = {
                'name'          : name,
                'cookie'        : self.cookieID,
                'last_logon'    : self.date,
                'voted'         : False
            }
            data = pl.DataFrame(data)

            # Combine the data together
            df = pl.concat([log, data], how = 'diagonal_relaxed')

            # Write the data to the cookie log sheet
            self.workSheet.set_dataframe(df.to_pandas(), (1,1))

            # If we submitted already, refresh the page
            if 'cookieSubmit' in st.session_state and st.session_state['cookieSubmit'] and name != '':
                st.session_state['cookieSubmit'] = False
                st.rerun()

        # If we do have the user, then update the last logon time
        else:
            self.updateUser()

    def updateUser(self, voted = False):
        '''Updates the user's last logon time'''
        # Try to change the vote status if the button was pressed
        try:
            voted = st.session_state['vote']
        except:
            pass

        # Get a dataframe of the current users
        df = pl.from_pandas(self.workSheet.get_as_df())

        # Find the row with the cookie in question
        row = df.with_row_index().filter(
            pl.col('cookie') == self.cookieID
        )['index'][0]

        # Update the user's last logon date
        df[row, 'last_logon'] = self.date

        # If the user has voted, update that field as well
        if voted:
            df[row, 'voted'] = True

        # Write back to the worksheet
        self.workSheet.set_dataframe(df.to_pandas(), (1,1))

    def resetVotes(self):
        '''Reset the voted status for all users'''
        # Get the dataframe of current cookies
        df = pl.from_pandas(self.workSheet.get_as_df())

        # Reset the values to False for the voted column
        df = df.with_columns(
            pl.col('voted').map_elements(
                lambda x: False, return_dtype = pl.Boolean
            )
        )

        # Write back to the sheet
        self.workSheet.set_dataframe(df.to_pandas(), (1,1))

    def voteButton(self):
        st.button('Vote', key = 'vote', on_click = self.updateUser)

    def resetButton(self):
        st.button('Reset', on_click = self.resetVotes)

class vote:
    '''Class to track user votes'''

    def __init__(self):
        # Set up the user
        self.user = cookie()

        # Set up the sheets
        self.votingPages()

        # Get the user's name
        df = pl.from_pandas(self.user.workSheet.get_as_df())

        # Filter for the user
        df = df.filter(pl.col('cookie') == self.user.cookieID)

        # Check that we got a result
        if len(df) > 0: 
            self.name = df['name'][0]

            # Set up the sheet to track votes
            self.voteSheet = self.sheet.sh[self.voteSheetNum]

            # Set up the sheet to track Elections
            self.electionSheet = self.sheet.sh[self.electionSheetNum]

    def votingPages(self):
        '''Get the Election and Vote sheet numbers'''
        # Set up the sheet
        self.sheet = self.user.sheet

        # Find our sheets
        n = 0
        found = 0

        # Loop until we find everything
        while True:

            # Get the name of the current sheet
            name = self.sheet.sh[n].title 

            # Check if it's one of the sheets we're looking for
            if name == 'Election':
                self.electionSheetNum = n
                found += 1
            elif name == 'Vote':
                self.voteSheetNum = n
                found += 1

            # If we've found all the items, exit
            if found >= 2:
                break
            
            # Increment
            n += 1

            # Error Condition
            if n > 100:
                st.error("Did not find the following sheets:")
                st.error("Election & Vote")
                break

    def vote(self, userVote):
        '''Take the vote information and write it to the sheet'''
        # Check if the user has voted already
        if self.checkVote() == True:
            return
        
        # Init the variable
        st.session_state['vote'] = False

        # Read in the current data
        df = pl.from_pandas(self.voteSheet.get_as_df())

        # Make a dataframe of the user's vote
        data = {
            'name'      : [],
            'vote_date' : [],
            'book'      : [],
            'rank'      : []
        }

        # Loop through the user's votes
        for key in userVote:
            # Ignore 'N/A' votes
            if userVote[key] == 'N/A':
                continue

            # Otherwise, add the data
            data['name'].append(self.name)
            data['vote_date'].append(self.user.date)
            data['book'].append(key)
            data['rank'].append(int(userVote[key]))

        # Make the dataframe
        data = pl.DataFrame(data)

        # Combine the data togther
        df = pl.concat([df, data], how = 'diagonal_relaxed')

        # Write the new data to the vote sheet
        self.voteSheet.set_dataframe(df.to_pandas(), (1,1))

        # Update the user's vote status
        st.session_state['vote'] = True
        self.user.updateUser()

    def checkVote(self):
        '''Check if the user has already voted'''
        # Pull the data
        df = pl.from_pandas(
            self.user.workSheet.get_as_df()
        )

        # Convert the voted status to an integer
        df = df.with_columns(pl.col('voted').replace({'FALSE' : 0, 'TRUE' : 1}).cast(pl.Int64))

        # Get the vote status for the user's name
        voteStatus = df.filter(
            pl.col('name') == self.name
        )['voted'].sum()

        # If anyone with the user's name has voted, that counts as this user having voted
        voteStatus = True if voteStatus >= 1 else False

        # Return the boolean
        return voteStatus

    def currentElection(self):
        '''Gets the current nominees for the current or previous election'''
        sheet = self.electionSheet
        df = pl.from_pandas(sheet.get_as_df())

        # Convert the date string to a datetime
        df = df.with_columns(
            pl.col('election_date').str.to_datetime('%d%b%Y')
        )

        # Get and return the most recent election_date data
        latestDate = df['election_date'].max()
        recent = df.filter(pl.col('election_date') == latestDate)
        return recent

class bookSummary:
    '''Pulls and writes the book summaries'''
    
    def __init__(self):
        self.apiKey = apiKey
        self.sheet = connection()
        self.bookSheet()

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

    def bookSheet(self):
        '''Sets the worksheet and sheet number for the Suggested Books Page'''
        # Figure out which sheet is the cookie log
        n = 0
        while True:
            name = self.sheet.sh[n].title 
            if name == 'Suggested Books':
                break
            n += 1

        # Save the data
        self.sheetNum = n

        self.workSheet = self.sheet.sh[self.sheetNum]

    def writeBookInfo(self, book, bookInfo):
        '''Writes the given book info to the google sheet
        NOTE: If a book already exists on the page, returns 1'''
        # Get the current book data
        df = pl.from_pandas(
            self.workSheet.get_as_df()
        )

        # Check if the book is on the list already
        if bookInfo['id'] in df['id'].unique().to_list():
            
            # Get the book's victory status
            victorious = df.filter(pl.col('id') == bookInfo['id'])['victorious'][0]

            # If the book is on the list, check if it's won before
            if victorious != '':
                st.toast(f"This book won already: {victorious}")

            # Otherwise, notify the user that the book was already on the list
            else:
                st.toast("This book is already on the list!")

            # Return 1 if the book was already on our list
            return 1

        # Otherwise, write the information to the sheet...

        # Get today's date
        today = datetime.datetime.today()

        # Make a dataframe
        data = pl.DataFrame({
            'book'              : book,
            'id'                : bookInfo['id'],
            'author'            : bookInfo['author'],
            'pages'             : bookInfo['pages'],
            'description'       : bookInfo['description'],
            'image'             : bookInfo['image'],
            'date_suggested'    : today.strftime('%d%b%Y'),
            'times_voted_on'    : 0,
            'nominated'         : False,
            'victorious'        : ''
        })

        # Get the last row of the current sheet
        cells = self.workSheet.get_all_values(include_tailing_empty_rows=False, include_tailing_empty=False, returnas='matrix')
        last_row = len(cells)

        # Append the row to the spreadsheet
        self.workSheet.insert_rows(last_row, number = 1, values = list(data.row(0)))

        # If success... party time
        st.balloons()

        # Return 0 on successful execution
        return 0

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


    def dbDisplayBookInfo(self, book):
        '''Displays the book information stored in the google sheet database'''
        # Get the data for this book
        df = pl.from_pandas(
            self.workSheet.get_as_df()
        ).filter(pl.col('book') == book)

        # Display the book title
        st.write(f'# {df['book']}')

        # Make the columns
        col1, col2, col3 = st.columns([0.25, 0.25, 0.5])

        # Display the image, if there is one
        image = df['image'][0]
        if image:
            with col1:
                st.image(image)

        # Display the book stats
        with col2:
            # Write the author
            st.write('##### By:')
            st.write(df['author'][0])

            # Write the number of pages
            st.write('##### Pages:')
            st.write(df['pages'][0])

        # Write the description of the book
        with col3:
            st.write('##### Description:')
            st.write(df['description'][0])

class election:
    '''Saves the current election nominees, starts elections, and resets voting status'''
    def __init__(self):
        self.sheet = connection()
        

if __name__ == '__main__':
    main()