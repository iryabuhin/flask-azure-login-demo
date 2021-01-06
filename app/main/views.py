from flask import request, render_template, redirect, url_for, abort, session, jsonify
from base64 import b64encode
import uuid
from functools import wraps
from datetime import datetime, timedelta
from . import main
from .. import microsoft
from .ictis_api import get_student_data
# from .verify_form import check_form_data
from app import mongo


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
                session.clear()
                print(
                    "Access Denied: Reason={}\nError={}".format(
                        response.get('error'),
                        request.get('error_description')
                    )
                )
                return redirect(url_for('.index'))
            else:
                session['microsoft_token'] = (response['access_token'], '')
                session['expires_at'] = datetime.now() + timedelta(seconds=int(response['expires_in']))
                session['refresh_token'] = response['refresh_token']
                return f(*args, **kwargs)
    return wrap


@main.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@main.route('/login', methods=['POST', 'GET'])
def login():
    if 'microsoft_token' in session:  # TODO: verify purpuose
        return redirect(url_for('.projects'))

    # Generate the guid to only accept initiated logins
    guid = str(uuid.uuid4())
    session['state'] = guid

    return microsoft.authorize(callback=url_for('.authorized', _external=True), state=guid)


@main.route('/logout', methods=['POST', 'GET'])
def logout():
    session.pop('microsoft_token', None)
    session.pop('state', None)
    return redirect(url_for('.index'))


@main.route('/login/authorized')
def authorized():
    response = microsoft.authorized_response()

    if response is None:
        return "Access Denied: Reason=%s\nError=%s" % (
            response.get('error'),
            request.get('error_description')
        )

    # Check response for state
    if str(session['state']) != str(request.args['state']):
        raise Exception('State has been messed with, end authentication')

    session['microsoft_token'] = (response['access_token'], '')
    session['expires_at'] = datetime.now() + timedelta(seconds=int(response['expires_in']))
    session['refresh_token'] = response['refresh_token']

    return redirect(url_for('.projects'))


@main.route('/projects')
@login_required
def projects():
    me = microsoft.get('me').data
    email = me.get('mail')

    # because azure doesnt work properly on localhost
    if email is None:
        email = me.get('givenName')

    student_data = get_student_data(email) # TODO добавить проверку на первый/второй курс

    pipeline = [
        {'$group': {
            '_id': '$mentorName',
            'projects': {'$push': {'name': '$name', '_id': '$_id'}}
        }}
    ]

    projects_collection = mongo.db.projects
    test = list(projects_collection.aggregate(pipeline))
    projects_by_mentor = {doc['_id']: doc['projects'] for doc in test}

    # profile_image_data = microsoft.get('me/photo/$value').data
    # image_b64 = b64encode(profile_image_data).decode('utf-8')

    return render_template('project_select.html', data=student_data, projects_by_mentor=projects_by_mentor)


@main.route('/form_response', methods=['POST'])
def form_response():
    if request.method == 'GET':
        abort(405)

    me = microsoft.get('me')
    microsoft_displayName = me.data['displayName']
    microsoft_mail = me.data['mail']
    user_group = get_student_data(microsoft_mail)
    user_data = f"{microsoft_displayName}, {user_group}"
    print(user_data)

    form_data = request.form
    form_project_theme = form_data['entry.1716975243']
    form_user_data = f"{form_data['entry.1846423724']}, {form_data['entry.1205430654']}"
    form_command_number = form_data['command_number']
    data_check = check_form_data(form_user_data=form_user_data,
                                 user_data=user_data,
                                 theme_project=form_project_theme,
                                 command=form_command_number)
    if not data_check:
        return "Некорректные данные формы. Проверьте ваше ФИО, группу, тему проекта и команду"
    status = join_team(theme=form_project_theme, command=form_command_number, data=user_data)
    print(status)
    return redirect(url_for('.answers', status=status))


@main.route('/answers/', methods=['GET', 'POST'])
def answers():
    status = request.args.get('status')
    return render_template('answers.html', status=status)


@microsoft.tokengetter
def get_microsoft_oauth_token():
    return session.get('microsoft_token')
