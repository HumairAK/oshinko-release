from flask import Blueprint, request, json, current_app as app
from ..tasks import worker
from ..util.post_schemas import schemas
from ..util.validator import validate_schema
from ..util.util import json_response, fetch_gh_info, fetch_dh_info


oshcli = Blueprint('oshinko_cli', __name__, url_prefix='/oshinko_cli')


@oshcli.route("/jenkins/build/start", methods=['POST'])
@validate_schema(schemas['oshinko_cli']['start_build'])
def start_build():
    data = request.data
    data_dict = json.loads(data)
    worker.oshinko_cli_jenkins_start_build.delay(
        data_dict['jenkins_host'], data_dict['jenkins_user'], data_dict['jenkins_psw'],
        data_dict['jenkins_job'], data_dict['oshinko_ver'])
    return json_response('Jenkins build start request sent.', 200)


# TODO: Need to be able to handle only responses to builds we started
# TODO: One solution: Use secrets as additional payload through notification
@oshcli.route("/jenkins/build/finish", methods=['POST'])
@validate_schema(schemas['oshinko_cli']['build_finish'], allow_unknown=True)
def finish_build():
    job = request.data
    job = json.loads(job)
    gh_repo_owner, repo_name = app.config['UPSTREAM_REPOS']['OSHINKO_CLI'].split('/')
    gh_user, gh_email, gh_token = fetch_gh_info(app)
    dh_repo, dh_token = fetch_dh_info(app, 'OSHINKO_CLI')

    # TODO: Some of these checks can be moved to cerberus validation
    is_final = job['build']['phase'] == 'FINALIZED'
    is_successful = 'status' in job['build'] and job['build']['status'] == 'SUCCESS'

    watch_build_task = worker.watch_autobuild.s(dh_repo, dh_token, 120, 45, False)

    if is_final and is_successful:
        worker.oshinko_cli_bin_release.apply_async((job, gh_repo_owner, repo_name, gh_user,
                                                    gh_email, gh_token), link=watch_build_task)

    return json_response('Received build finish notification. Release task started.', 200)

