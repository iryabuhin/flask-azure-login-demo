from flask import request, render_template, redirect, url_for, abort, session
from base64 import b64encode
import uuid
from os import getenv
import requests
from functools import wraps
from datetime import datetime, timedelta
from . import main
from .. import microsoft
from .google_sheets import *

# Implements refresh token logic, which is lacking in flask_oauthlib, oh pity
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

    return redirect(url_for('.projects'))


@main.route('/me')
@login_required
def me():
    me = microsoft.get('/beta/me/profile')
    data = me.data
    return render_template('me.html', me=data)


@main.route('/projects')
@login_required
def projects():
    me = microsoft.get('me')
    # profile_image_data = microsoft.get('me/photo/$value').data
    # image_b64 = b64encode(profile_image_data).decode('utf-8')

    return render_template('form.html', data=me.data)


@main.route('/form_response', methods=['POST'])
def form_response():
    if request.method == 'GET':
        abort(405)

    form_data = request.form
    project_theme = form_data['entry.1716975243']
    user_data = f"{form_data['entry.1846423724']}, {form_data['entry.1205430654']}"
    command_number = form_data['command_number']
    print(project_theme)
    print(user_data)
    print(command_number)
    status = join_team(theme=project_theme, command=command_number, data=user_data)
    print(status)
    return redirect(url_for('.answers', status=status))


@main.route('/answers/', methods=['GET', 'POST'])
def answers():
    status = request.args.get('status')
    return render_template('answers.html', status=status)

@microsoft.tokengetter
def get_microsoft_oauth_token():
    return session.get('microsoft_token')
