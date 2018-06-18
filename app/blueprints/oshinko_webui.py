from flask import Blueprint, json, current_app as app
from ..tasks import worker

oshwebui = Blueprint('oshinko_webui', __name__, url_prefix='/oshinko_webui')


@oshwebui.route("/update/version/<version>", methods=['POST'])
def update_version(version):
    oshinko_webui = app.config['UPSTREAM_REPOS']['OSHINKO_WEBUI']
    user, repo = oshinko_webui['REPO'].split('/')
    token = oshinko_webui['TOKEN']

    dockerhub_repo = app.config['DOCKERHUB_REPOS']['OSHINKO_WEBUI']['REPO']
    dockerhub_token = app.config['DOCKERHUB_REPOS']['OSHINKO_WEBUI']['TOKEN']
    watch_build_task = worker.watch_autobuild.s(dockerhub_repo, dockerhub_token, 120, 45, False)

    worker.oshinko_webui_version_update.apply_async((user, repo, token, version),
                                                    link=watch_build_task)

    r = json.dumps({'api': '/oshinko_webui', 'Status:': 'OK', 'Message': 'Job started'})
    response = app.response_class(
        response=r,
        status=200,
        mimetype='application/json'
    )
    return response

