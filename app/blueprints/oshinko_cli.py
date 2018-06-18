from flask import Blueprint, request, json, current_app as app
from ..tasks import worker
from ..util.post_schemas import schemas
from ..util.validator import validate_schema

oshcli = Blueprint('oshinko_cli', __name__, url_prefix='/oshinko_cli')


@oshcli.route("/update/master", methods=['GET'])
def update_image():
    response = json.dumps({'Status:': 'OK', 'msg': 'Not implemented.'})
    return response


@oshcli.route("/jenkins/build/start", methods=['POST'])
@validate_schema(schemas['oshinko_cli']['start_build'])
def start_build():
    data = request.data
    data_dict = json.loads(data)
    worker.oshinko_cli_jenkins_start_build.delay(
        data_dict['jenkins_host'], data_dict['jenkins_user'], data_dict['jenkins_psw'],
        data_dict['jenkins_job'], data_dict['oshinko_ver'])
    return json.dumps({'Status:': 'OK', 'msg': 'jenkins build start request sent.'})


# TODO: Need to be able to handle only responses to builds we started
@oshcli.route("/jenkins/build/finish", methods=['POST'])
@validate_schema(schemas['oshinko_cli']['build_finish'], allow_unknown=True)
def finish_build():
    job = request.data
    job = json.loads(job)
    oshinko_cli = app.config['UPSTREAM_REPOS']['OSHINKO_CLI']

    user, repo_name = oshinko_cli['REPO'].split('/')
    token = oshinko_cli['TOKEN']

    # TODO: Some of these checks can be moved to cerberus validation
    is_final = job['build']['phase'] == 'FINALIZED'
    is_successful = 'status' in job['build'] and job['build']['status'] == 'SUCCESS'

    dockerhub_repo = app.config['DOCKERHUB_REPOS']['OSHINKO_CLI']['REPO']
    dockerhub_token = app.config['DOCKERHUB_REPOS']['OSHINKO_CLI']['TOKEN']

    watch_build_task = worker.watch_autobuild.s(dockerhub_repo, dockerhub_token, 120, 45, False)

    if is_final and is_successful:
        worker.oshinko_cli_bin_release.apply_async((job, user, repo_name, token),
                                                   link=watch_build_task)

    res = json.dumps({
        'Status:': 'OK',
        'msg': 'Received build finish notification. Release task started.'
    })
    return res
