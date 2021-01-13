from typing import Dict

import requests
from requests.auth import HTTPBasicAuth
from flask import current_app
from app import cache

STUDY_LEVEL_NAMES = {
    'специалист': 'КТсо',
    'бакалавр': 'КТбо',
    'прикладной бакалавр': 'КТбо'
}


# @cache.memoize(timeout=15*60)
def get_student_data(email: str) -> Dict[str, str]:
    response = requests.get(
        current_app.config['ICTIS_API_URL'],
        params={'email': email},
        auth=HTTPBasicAuth(
            current_app.config['ICTIS_API_LOGIN'],
            current_app.config['ICTIS_API_PASSWORD']
        )
    )

    data = response.json()

    if data.get('student') is None or \
            data.get('student').get('levelLearn').lower() not in STUDY_LEVEL_NAMES.keys():
        return {}

    data = data['student']

    group = '{}{}-{}'.format(
        STUDY_LEVEL_NAMES[data.get('levelLearn').lower()],
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
