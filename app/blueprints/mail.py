from flask import Blueprint, Response, json

mail = Blueprint('mail', __name__, url_prefix='/mail')


# TODO: IMPLEMENT
@mail.route("/release", methods=['GET'])
def create_release_branch():

    # Send a release email to bigdatateam et al

    r = json.dumps({'Status:': 'OK'})
    return Response(r, status=200, mimetype="application/json")