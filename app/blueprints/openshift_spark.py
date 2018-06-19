from flask import Blueprint, json, current_app as app
from ..tasks import worker
from ..util.util import json_response, fetch_gh_info, fetch_dh_info

ospark = Blueprint('ospark', __name__, url_prefix='/ospark')


@ospark.route("/update/version/<version>", methods=['POST'])
def update_master(version):
    gh_repo_owner, repo_name = app.config['UPSTREAM_REPOS']['OPENSHIFT_SPARK'].split('/')
    gh_user, gh_email, gh_token = fetch_gh_info(app)
    dh_repo, dh_token = fetch_dh_info(app, 'OPENSHIFT_SPARK')

    watch_build_task = worker.watch_autobuild.s(dh_repo, dh_token, 120, 45, False)

    worker.openshift_spark_update.apply_async((gh_repo_owner, repo_name, gh_user,
                                               gh_email, gh_token, version), link=watch_build_task)
    return json_response('Openshift Spark update task queued.', 200)
