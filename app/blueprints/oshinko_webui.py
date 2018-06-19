from flask import Blueprint, json, current_app as app
from ..tasks import worker
from ..util.util import json_response, fetch_gh_info, fetch_dh_info

oshwebui = Blueprint('oshinko_webui', __name__, url_prefix='/oshinko_webui')


@oshwebui.route("/update/version/<version>", methods=['POST'])
def update_version(version):

    gh_repo_owner, repo_name = app.config['UPSTREAM_REPOS']['OSHINKO_WEBUI'].split('/')
    gh_user, gh_email, gh_token = fetch_gh_info(app)
    dh_repo, dh_token = fetch_dh_info(app, 'OSHINKO_WEBUI')

    watch_build_task = worker.watch_autobuild.s(dh_repo, dh_token, 120, 45, False)

    worker.oshinko_webui_version_update.apply_async((gh_repo_owner, repo_name, gh_user,
                                                     gh_email, gh_token, version),
                                                    link=watch_build_task)

    return json_response('Oshinko-WebUI tag push task started', 200)


