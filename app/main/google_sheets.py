from pprint import pprint
import httplib2
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

basedir = os.path.abspath(os.path.dirname(__file__))

CREDENTIALS_FILE = basedir + '\creds.json'

spreadsheet_id = '1pYu27lthhJRhhXJbGnLpkPOt_-iVrxCIqL5kDVdKcdI'

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    CREDENTIALS_FILE,
    ['https://www.googleapis.com/auth/spreadsheets',
     'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http = httpAuth)

def is_in_team(data):
    flag = False
    values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range="B9:AC34",
        majorDimension='COLUMNS'
    ).execute()
    table_data = values['values'][0]
    for i in range(len(table_data)):
        table_data[i] = table_data[i].rstrip()
    if data in values['values'][0]:
        flag = True
    return flag

def get_command_squad(theme_column_index, row_index_range):
    range_of_values = f'{theme_column_index}{row_index_range[0]}:{theme_column_index}{row_index_range[1]}'
    values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_of_values,
        majorDimension='COLUMNS'
    ).execute()
    squad = values['values'][0]
    return squad


def join_team(theme, command, data):
    project_themes = basedir + "\project_themes.json"
    with open(project_themes, "r", encoding='utf-8') as read_file:
        projects_columns_dict = json.load(read_file)

    print(projects_columns_dict)
    command_number = {"Команда 1": [9, 16], "Команда 2": [18, 25], "Команда 3": [27, 34]}
    theme_column_index = projects_columns_dict[theme]
    row_index_range = command_number[command]
    team_squad = get_command_squad(theme_column_index, row_index_range)
    print(team_squad)
    if is_in_team(data):
        status = 'in_team'
        return status
    else:
        if 'x' in team_squad:
            pos = team_squad.index('x') + command_number[command][0]
            write_index = f"{theme_column_index}{pos}"
            try:
                values = service.spreadsheets().values().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={
                        "valueInputOption": "USER_ENTERED",
                        "data": [
                            {"range": write_index,
                             "majorDimension": "ROWS",
                             "values": [[data]]},
                    ]
                    }
                ).execute()
                status = 'success'
                return status
            except:
                status = 'error'
                return status
        else:
            status = 'no_places'
            return status

