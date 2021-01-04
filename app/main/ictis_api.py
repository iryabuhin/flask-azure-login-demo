from typing import Dict

import requests
from requests.auth import HTTPBasicAuth
from flask import current_app
import json

STUDY_LEVEL_NAMES = {'Специалист': 'КТсо', 'Бакалавр': 'КТбо'}


def get_student_data(email: str) -> Dict[str, str]:
    response = requests.get(
        current_app.config['ICTIS_API_URL'],
        params={'email': email},
        auth=HTTPBasicAuth(
            current_app.config['ICTIS_API_LOGIN'],
            current_app.config['ICTIS_API_PASSWORD']
        )
    )

    data = json.loads(response.text)['student']
    group = '{}{}-{}'.format(
        STUDY_LEVEL_NAMES[data['levelLearn']],
        data['grade'],
        data['stGroup']
    )
    full_name = '{} {} {}'.format(
        data['lastName'],
        data['firstName'],
        data['secondName']
    )
    data.update({
        'fullName': full_name,
        'group': group,
        'email': email
    })

    return data
