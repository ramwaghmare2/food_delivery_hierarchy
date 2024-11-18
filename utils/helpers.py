from flask import jsonify

def format_response(status=200, message=None, data=None):
    response = {'status': status, 'message': message}
    if data:
        response['data'] = data
    return jsonify(response), status

def handle_error(e):
    return format_response(status=500, message=str(e))