from flask import Blueprint, json, current_app as app
from ..tasks import worker
from ..util.util import json_response, fetch_gh_info, fetch_dh_info

ocproxy = Blueprint('oc_proxy', __name__, url_prefix='/oc_proxy')


@ocproxy.route("/update/version/<version>", methods=['POST'])
def update_version(version):
    gh_repo_owner, repo_name = app.config['UPSTREAM_REPOS']['OC_PROXY'].split('/')
    gh_user, gh_email, gh_token = fetch_gh_info(app)
    dh_repo, dh_token = fetch_dh_info(app, 'OC_PROXY')
    watch_build_task = worker.watch_autobuild.s(dh_repo, dh_token, 120, 45, False)

    worker.oc_proxy_version_update.apply_async((gh_repo_owner, repo_name, gh_user,
                                                gh_email, gh_token, version), link=watch_build_task)

    return json_response('OC Proxy tag push task started', 200)
