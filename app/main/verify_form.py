import json
import os.path
from config import basedir
from project_themes import PROJECT_THEMES


COMMAND_NUMBERS = {"Команда 1": [9, 16], "Команда 2": [18, 25], "Команда 3": [27, 34]}

def check_form_data(form_user_data, user_data, theme_project, command):
    flag = True
    # project_themes = './project_themes.json'

    # with open(project_themes, "r", encoding='utf-8') as read_file:
    #     PROJECT_THEMES = json.load(read_file)

    if not (form_user_data.lower() == user_data.lower()):
        flag = False

    if PROJECT_THEMES.get(theme_project) is None:
        flag = False

    print(COMMAND_NUMBERS)

    if COMMAND_NUMBERS.get(command) is None:
        flag = False

    return flag
