import pickle
import os.path
import re
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource
from google.auth.transport.requests import Request
from typing import Dict, List, Optional, Any
from json import JSONDecodeError
from googleapiclient.errors import HttpError, Error

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


def sheets_write_to_cell(service: Resource, spreadsheet_id: str, cell: str, value: str) -> Dict[str, str]:
    try:
        result: Dict = service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={
                'valueInputOption': 'RAW',
                'includeValuesInResponse': True,
                'data': [
                    {
                        'range': cell,
                        'majorDimension': 'ROWS',
                        'values': [[value]]
                    },
                ]
            }
        ).execute()

        if result.get('totalUpdatedCells') == 1:
            result.update({'index': cell})
            return {'status': 'success', 'result': result}

    except HttpError as e:
        return {'status': 'error', 'error_name': 'http_error', 'details': e.error_details}
    except Error as e:
        return {'status': 'error', 'error_name': 'api_error', 'details': {'type': 'unknown'}}
    except:
        raise


def sheets_team_add_member(value: str, team_cell_index: str, team_empty_slots: int) -> Dict[str, str]:
    service = get_sheets_service()

    col = re.search('[A-Z]+', team_cell_index).group(0)

    team_name_row = int(re.search('[0-9]+', team_cell_index).group(0))
    places_taken = TEAM_MAX_SIZE - team_empty_slots
    row = team_name_row + places_taken
    cell_index = col + str(row)

    result = sheets_write_to_cell(service, os.environ.get('SPREADSHEET_ID'), cell_index, value)

    return result

