from flask import jsonify

def bad_request(message: str):
    resp = jsonify({'error': 'bad request', 'message': message})
    resp.status_code = 400
    return resp

def unauthorized(message: str):
    resp = jsonify({'error': 'unauthorized', 'message': message})
    resp.status_code = 401
    return resp

def forbidden(message: str):
    resp = jsonify({'error': 'forbidden', 'message': message})
    resp.status_code = 403
    return resp
