from flask import Blueprint, Response, json
from ..util.util import json_response
home = Blueprint('root', __name__)


# TODO: IMPLEMENT
@home.route("/")
def root():
    """ Give a generic response. """
    return json_response('OK', 200)
