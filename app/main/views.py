from flask import request, render_template, redirect, url_for, abort, session, jsonify, current_app
from base64 import b64encode
import uuid
from functools import wraps
from datetime import datetime, timedelta
from typing import Dict, List
from . import main
from .. import microsoft
from .ictis_api import get_student_data, STUDY_LEVEL_NAMES
from app import mongo
from app import cache
from flask_required_args import required_data
from flask_oauthlib.client import OAuthException
from pymongo import CursorType


# @cache.cached(timeout=5*60, key_prefix='projects_by_mentor')
def get_projects_by_mentor() -> Dict[str, List[Dict[str, str]]]:
    result = dict()
    pipeline = [{'$group': {'_id': '$mentorName', 'projects': {'$push': {'name': '$name', '_id': '$_id'}}}}]

    collection = mongo.db.projects
    docs_iter = collection.aggregate(pipeline, allowDiskUse=True)
    for doc in docs_iter:
        result.update({doc['_id']: doc['projects']})

    return result


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'microsoft_token' not in session:
            return redirect(url_for('.login'))

        if session['expires_at'] > datetime.now():
            return f(*args, **kwargs)
        elif 'refresh_token' in session:
            # Try to get a Refresh Token
            data = dict()
            data['grant_type'] = 'refresh_token'
            data['refresh_token'] = session['refresh_token']
            data['client_id'] = microsoft.consumer_key
            data['client_secret'] = microsoft.consumer_secret

            response = (microsoft.post(microsoft.access_token_url, data=data)).data

            if response is None:
                raise OAuthException
            elif response.get('error'):
                session.clear()

                current_app.logger.error(
                    "Azure Access Denied: Reason={}\nError={}".format(
                        response.get('error'),
                        response.get('error_description')
                    )
                )

                return render_template(
                    'error.html',
                    error_header=response.get('error'),
                    error_message=response.get('error_description')
                )
            else:
                session['microsoft_token'] = (response['access_token'], '')
                session['expires_at'] = datetime.now() + timedelta(seconds=int(response['expires_in']))
                session['refresh_token'] = response['refresh_token']
                return f(*args, **kwargs)
    return wrap


@main.route('/', methods=['GET'])
def index():
    show_logout = None
    if 'microsoft_token' in session:
        show_logout = True

    return render_template('index.html', show_logout=show_logout)


@main.route('/login', methods=['POST', 'GET'])
def login():
    if 'microsoft_token' in session:  # TODO: verify purpuose
        return redirect(url_for('.projects'))

    # Generate the guid to only accept initiated logins
    # guid = str(uuid.uuid4())
    # session['state'] = guid

    # return microsoft.authorize(callback=url_for('.authorized', _external=True), state=guid)
    return microsoft.authorize(callback=url_for('.authorized', _external=True))


@main.route('/logout', methods=['POST', 'GET'])
def logout():
    session.pop('microsoft_token', None)
    # session.pop('state', None)
    return redirect(url_for('.index'))


@main.route('/login/authorized')
def authorized():
    response = microsoft.authorized_response()

    if response is None:
        current_app.logger.error('No response received from microsoft, context: ' + 'Args: ' + ' '.join(request.args))
        return render_template(
            'error.html',
            error_header='Ошибка авторизации Microsoft',
            error_message='При попытке авторизации произошла ошибка. Попробуйте выйти и затем снова авторизоваться.',
            show_logout=True
        )

    # Check response for state
    # if str(session['state']) != str(request.args['state']):
    #     raise Exception('State has been messed with, end authentication')

    session['microsoft_token'] = (response['access_token'], '')
    session['expires_at'] = datetime.now() + timedelta(seconds=int(response['expires_in']))
    session['refresh_token'] = response['refresh_token']

    return redirect(url_for('.projects'))


def render_error_template(error_header: str, error_message: str, **kwargs):
    return render_template(
        'error.html',
        error_header=error_header,
        error_message=error_message,
        **kwargs
    )


@main.route('/projects')
@login_required
def projects():

    if current_app.config['PROJECT_REGISTRATION_DISABLED']:
        return render_error_template('Запись закрыта', 'Запись на творческие проекты в данный момент закрыта.', show_logout=True)

    me = microsoft.get('me').data
    email = me.get('mail')

    # because azure doesnt work properly on localhost
    if email is None:
        email = me.get('givenName')

    error_occurred = False
    error_message = error_header = ''

    student_data = get_student_data(email)

    if not student_data \
            or student_data['levelLearn'].lower() not in STUDY_LEVEL_NAMES.keys() \
            or int(student_data['grade']) > int(current_app.config['STUDENT_GRADE_MAX']):
        error_occurred = True
        error_header = 'Ошибка'
        error_message = 'Запись открыта только для студентов первого курса ИКТИБ ИТА ЮФУ'

    if error_occurred:
        return render_error_template(error_header, error_message, show_logout=True)

    doc = mongo.db.projects.find_one(
        filter={'teams.members.fullName': student_data['fullName']},
        projection={'name': 1, 'teams.name': 1}
    )

    if doc:
        return render_error_template(
            'Вы уже записаны на проект',
            'Вы уже записаны на творческий проект "{}"'.format(doc.get('name')),
            show_logout=True
            )

    projects_by_mentor = get_projects_by_mentor()

    # работает приблизительно в 5 раз быстрее, но требует дополнительной обработки
    # docs = list(mongo.db.projects.find(cursor_type=CursorType.EXHAUST).sort([('$natural', 1)]))

    # profile_image_data = microsoft.get('me/photo/$value').data
    # image_b64 = b64encode(profile_image_data).decode('utf-8')

    return render_template('projectSelect.html', data=student_data, projects_by_mentor=projects_by_mentor, show_logout=True)


@main.route('/success', methods=['GET'])
def after_successful_team_join():
    team_number = request.args.get('team_number')
    cell_index = request.args.get('cell_index')
    project_name = request.args.get('project_name')

    if any(arg is None for arg in [team_number, cell_index, project_name]):
        return jsonify({'status': 'error', 'message': 'not all params are present in the query string'}), 400

    sheet_url = 'https://docs.google.com/spreadsheets/d/{}/view#gid=0&range={}'.format(
        current_app.config['SPREADSHEET_ID'],
        cell_index
    )

    return render_template(
        'success.html',
        cell_index=cell_index,
        project_name=project_name,
        team_number=team_number,
        sheet_url=sheet_url,
        show_logout=True
    )


@microsoft.tokengetter
def get_microsoft_oauth_token():
    return session.get('microsoft_token')
