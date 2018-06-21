from flask import Blueprint, Response, json
from ..util.util import json_response
from ..tasks import worker


home = Blueprint('root', __name__)


# TODO: IMPLEMENT
@home.route("/")
def root():
    """ Give a generic response. """
    worker.tester.delay()
    return json_response('OK', 200)
