from flask import Blueprint, json, current_app as app
from ..tasks import worker
from ..util.util import json_response, fetch_gh_info, fetch_dh_info

# from ..util.post_schemas import schemas
# from ..util.validator import validate_schema

ospark = Blueprint('ospark', __name__, url_prefix='/ospark')


# TODO: Add watchbuild task in chain
@ospark.route("/update/version/<version>", methods=['POST'])
def update_master(version):
    gh_repo_owner, repo_name = app.config['UPSTREAM_REPOS']['OPENSHIFT_SPARK'].split('/')
    gh_user, gh_email, gh_token = fetch_gh_info(app)
    dh_repo, dh_token = fetch_dh_info(app, 'OPENSHIFT_SPARK')

    worker.openshift_spark_update.delay(gh_repo_owner, repo_name, gh_user, gh_email, gh_token, version)
    return json_response('Openshift Spark update task queued.', 200)
