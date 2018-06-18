from flask import Blueprint, json, current_app as app
from ..tasks import worker
# from ..util.post_schemas import schemas
# from ..util.validator import validate_schema

ospark = Blueprint('ospark', __name__, url_prefix='/ospark')


# @validate_schema(schemas['openshift_spark']['update'])
@ospark.route("/update/version/<version>", methods=['POST'])
def update_master(version):
    openshift_spark = app.config['UPSTREAM_REPOS']['OPENSHIFT_SPARK']
    user, repo = openshift_spark['REPO'].split('/')
    token = openshift_spark['TOKEN']
    worker.openshift_spark_update.delay(user, repo, token, version)

    r = json.dumps({'api': '/ospark', 'Status:': 'OK', 'Message': 'Job started'})
    response = app.response_class(
        response=r,
        status=200,
        mimetype='application/json'
    )

    return response
