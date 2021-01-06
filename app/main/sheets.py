import pickle
import os.path
import re
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource
from google.auth.transport.requests import Request
from flask import current_app
from json import JSONDecodeError
from config import basedir

TEAM_MAX_SIZE = 8
GOOGLE_CREDENTIALS = os.environ.get('GOOGLE_CREDENTIALS')
SCOPES =[
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


def get_sheets_service() -> Resource:
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    return service


def sheets_team_add_member(value: str, team_cell_index: str, team_empty_slots: int):
    service = get_sheets_service()

    col = re.search('[A-Z]+', team_cell_index).group(0)

    team_name_row = int(re.search('[0-9]+', team_cell_index).group(0))
    places_taken = TEAM_MAX_SIZE - team_empty_slots
    row = team_name_row + places_taken + 1
    index = col + str(row)


    values = service.spreadsheets().values().batchUpdate(
        spreadsheetId=os.environ.get('SPREADSHEET_ID'),
        body={
            'valueInputOption': 'USER_ENTERED',
            'data': [
                {
                    'range': index,
                    'majorDimension': 'ROWS',
                    'values': [[value]]},
                ]
            }
    ).execute()

    return index


