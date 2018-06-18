from flask import Blueprint, json, current_app as app
from ..tasks import worker

ocproxy = Blueprint('oc_proxy', __name__, url_prefix='/oc_proxy')


@ocproxy.route("/update/version/<version>", methods=['POST'])
def update_master(version):
    oc_proxy = app.config['UPSTREAM_REPOS']['OC_PROXY']
    user, repo = oc_proxy['REPO'].split('/')
    token = oc_proxy['TOKEN']

    dockerhub_repo = app.config['DOCKERHUB_REPOS']['OC_PROXY']['REPO']
    dockerhub_token = app.config['DOCKERHUB_REPOS']['OC_PROXY']['TOKEN']
    watch_build_task = worker.watch_autobuild.s(dockerhub_repo, dockerhub_token, 120, 45, False)

    worker.oc_proxy_version_update.apply_async((user, repo, token, version),
                                               link=watch_build_task)

    r = json.dumps({'api': '/oshinko_webui', 'Status:': 'OK', 'Message': 'Job started'})
    response = app.response_class(
        response=r,
        status=200,
        mimetype='application/json'
    )
    return response
