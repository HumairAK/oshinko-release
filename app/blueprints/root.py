from flask import Blueprint, Response, json

home = Blueprint('root', __name__)


# TODO: IMPLEMENT
@home.route("/")
def root():
    """ Give a generic response. """
    r = json.dumps({'Status:': 'OK', 'route': '/'})
    return Response(r, status=200, mimetype="application/json")
