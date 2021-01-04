from typing import Optional, Dict, Union, List
from flask import jsonify, request, current_app, url_for, Response
from . import api
from .. import mongo_client


def find_project_by_name(name: str) -> Dict[str, Union[str, List[Dict[str, str]]]]:
    coll = get_projects_collection()
    proj = coll.find_one(filter={'name': name})
    return proj


def find_not_full_teams_for_project(project_doc: Dict):
    teams_not_empty = list()
    for team in project_doc.get('teams'):
        if not team.get('isFull'):
            teams_not_empty.append(team)

    return teams_not_empty


def get_projects_collection():
    db = mongo_client[current_app.config['MONGO_DBNAME']]
    collection = db['projects']

    return collection


def json_response(status: str, message: str,
                  data: Dict = None,
                  status_code: int = None) -> Response:
    response: Response = jsonify({
        'status': status,
        'message': message,
        'data': data
    })
    if status_code is not None:
        response.status_code = status_code

    return response


def success(message: str, data: Dict) -> Response:
    return json_response('success', message, data=data)


def error(message: str, status_code: int = None) -> Response:
    return json_response('error', message, status_code=status_code)


@api.route('/api/projects/available', methods=['GET'])
def check_project_availability():
    project_name = request.args.get('projectName')

    if project_name is None:
        return error('no project name provided in query')

    proj = find_project_by_name(project_name)

    if not proj:
        return error('project with name "{}" not found'.format(project_name))

    if proj.get('availableForJoin'):
        teams_not_full = find_not_full_teams_for_project(proj)
        return success('found', data={'teams': teams_not_full})
    else:
        return error('Записаться на данный проект невозможно, пожалуйста, выберите другой проект из списка')

