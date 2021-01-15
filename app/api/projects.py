from typing import Optional, Dict, Union, List
from flask import jsonify, request, current_app, url_for, redirect, render_template, Response
from . import api
from app import mongo
from bson.objectid import ObjectId
from pymongo.errors import PyMongoError, OperationFailure
from pymongo import ReturnDocument
from app.main.sheets import sheets_team_add_member
from flask_required_args import required_data

def get_project_by_id(id: str, fields: List[str] = None) -> Dict:
    projection = None
    if fields is not None:
        projection = {field: 1 for field in fields}
    try:
        proj = mongo.db.projects.find_one(filter={'_id': ObjectId(id)}, projection=projection)
    except OperationFailure as e:
        return error('database operation error', 500, data={'code': e.code, 'details': e.details})
    except PyMongoError as e:
        return error('database error', 500)

    if not proj:
        return error('Проект не найден')

    return proj


def get_project_by_name(query: str) -> Dict:
    try:
        doc = mongo.db.projects.find({'$text': {'$search': query}})
    except OperationFailure as e:
        return error('database operational error', 500, data=[e.code, e.details])

    return success('found', data=list(doc))


def json_response(status: str, message: str,
                  data: Dict = None,
                  status_code: int = None,
                  **kwargs) -> Response:
    response: Response = jsonify({
        'status': status,
        'message': message,
        'data': data,
        **kwargs
    })
    if status_code is not None:
        response.status_code = status_code

    return response


def success(message: str, data: Dict, **kwargs) -> Response:
    return json_response('success', message, data=data, **kwargs)


def error(message: str, status_code: int = None, **kwargs) -> Response:
    return json_response('error', message, status_code=status_code, **kwargs)


@api.route('/api/projects/<id>/', methods=['GET'])
def projects_get(id: str):
    return get_project_by_id(id)


@api.route('/api/projects/find/<query>', methods=['GET'])
def get_by_name_proj(query: str):
    return get_project_by_name(query)


@api.route('/api/projects/<id>/available', methods=['GET'])
def check_project_availability(id: str):
    proj = get_project_by_id(id)

    if proj.get('availableForJoin'):
        return success('found', data={'teams': proj.get('teams')})
    else:
        return error('Записаться на данный проект невозможно, пожалуйста, выберите другой проект из списка')


@api.route('/api/projects/<id>/teams', methods=['GET'])
def get_project_teams(id: str):
    pass


@api.route('/api/projects/<id>/join', methods=['PUT'])
@required_data
def join_project(id: str, name: str, group: str, team: str):
    count = mongo.db.projects.count_documents({'teams.members.fullName': name})

    if count >= 1:
        proj = get_project_by_id(id, fields=['name'])
        return error(f'Вы уже записаны на проект "{proj["name"]}"')

    # названия команд в формате "Команда N (свободных мест: P)"
    team_number = int(team.split()[1]) - 1
    document_team_field_string = f'teams.{str(team_number)}.members'
    
    doc = get_project_by_id(id, fields=['teams.members', 'teams.emptySlots'])

    team = doc.get('teams')[team_number]
    if team.get('emptySlots') <= 0:
        return error(f'В команде №{str(team_number)} нет свободных мест')
    
    updated_document = mongo.db.projects.find_one_and_update(
        {'_id': ObjectId(id)},
        {
            # добавить участника в команду с номером team_number
            '$push': {
                document_team_field_string: {
                    'fullName': name,
                    'group': group
                }
            },
            # уменьшить количество свободных мест в этой команде на единицу
            '$inc': {
                f'teams.{str(team_number)}.emptySlots': -1
            }
        },
        return_document=ReturnDocument.AFTER
    )

    insert_result = sheets_team_add_member(
        f'{name}, {group}',
        updated_document['teams'][team_number]['sheetCellIndex'],
        updated_document['teams'][team_number]['emptySlots'] + 1
    )

    if insert_result['status'] == 'success':
        insert_result = insert_result['result']

        return success('insertion successful', data={
            'cellIndex': insert_result.get('index'),
            'teamNumber': int(team_number) + 1,
            'projectName': updated_document['name']
        })
    elif insert_result['status'] == 'error':
        return error(message=insert_result['message'])

    return error('insertion failed due to an unknown error')
