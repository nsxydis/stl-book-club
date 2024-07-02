import streamlit as st
from streamlit_cookies_controller import CookieController
import polars as pl
from rank import connection
import datetime

def main():
    # Set up the cookie class
    user = cookie()
    
    # Set up the controller
    controller = CookieController()

    # Set a cookie
    controller.set('cookie', 'voter')

    # Get all cookies
    cookies = controller.getAll()
    cookieID = cookies['ajs_anonymous_id']

    # Check the cookie log
    cookieLog(cookieID)

    # Get a cookie
    cookie = controller.get('cookie_name')

class cookie():
    '''Cookie Class to store and update user info'''

    def __init__(self):
        '''Set up the cookie infromation for the user'''
        # Establish connection
        self.sheet = connection()

        # Get the sheetNum variable
        self.cookieSheet()

        # Save the workSheet for the Cookie Log
        self.workSheet = self.sheet[self.sheetNum]

        # Set up the cookie for this user
        controller = CookieController()

        # Set a cookie
        controller.set('cookie', 'voter')

        # Get all cookies
        cookies = controller.getAll()

        # Set the cookie ID for this user
        self.cookieID = cookies['ajs_anonymous_id']

        # Get today's date and convert to ddMMMyyy
        today = datetime.datetime.today()
        self.date = today.strftime('%d%b%Y')

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
            
        # Make the dataframe to add to our log
        data = {
            'name'          : name,
            'cookie'        : self.cookieID,
            'last_logon'    : self.date,
            'voted'         : 'FALSE'
        }
        data = pl.DataFrame(data)

        # Combine the data together
        df = pl.concat([log, data], how = 'diagonal_relaxed')

        # Write the data to the cookie log sheet
        self.workSheet.set_dataframe(df.to_pandas(), (1,1))



def cookieSheet():
    '''Returns the sheet and number for the cookie log'''
    # Establish connection to the sheet
    sheet = connection()

    # Figure out which sheet is the cookie log
    n = 0
    while True:
        name = sheet.sh[n].title 
        if name == 'User Log':
            break
        n += 1

    # Return the data
    return sheet, n
    
def cookieLog(cookie):
    '''Get, check, and write to the cookie log'''
    # Get the worksheet and sheet number for the log
    sheet, n = cookieSheet()

    # Pull the cookie log
    log = pl.from_pandas(sheet.sh[n].get_as_df())

    # Check if our cookie is on there already
    check = log.filter(pl.col('cookie') == cookie)
    
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
        
        # Make the dataframe to add to our log
        today = datetime.datetime.today()
        data = {
            'name'          : name,
            'cookie'        : cookie,
            'last_logon'    : today.strftime('%d%b%Y'),
            'voted'         : 'FALSE'
        }
        data = pl.DataFrame(data)

        # Combine the data together
        df = pl.concat([log, data], how = 'diagonal_relaxed')

        # Write the data to the cookie log sheet
        sheet.sh[n].set_dataframe(df.to_pandas(), (1,1))

def updateUser(cookie):
    '''Updates the user's last logon'''
    # Get the cookie log info
    sheet, n = cookieSheet()

    # Pull the dataframe
    df = pl.from_pandas(sheet.sh[n].get_as_df())

    # Find the row with the cookie in question
    row = df.with_row_index().filter(
        pl.col('cookie') == cookie
    )['index'][0]

    # Update the logon

    df.with_row_index()


def resetVotes():
    '''Resets everyone's voted status to False'''

if __name__ == '__main__':
    main()