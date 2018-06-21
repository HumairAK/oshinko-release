from flask import Blueprint, json, current_app as app
from ..util.util import json_response
from ..models.models import \
    db, SessionContext, OpenshiftSpark, OshinkoCli, OcProxy, OshinkoWebUi, OshinkoSti
from datetime import datetime

session = Blueprint('session', __name__, url_prefix='/session')


@session.route("/create", methods=['POST'])
def create():
    date_now = datetime.now()

    openshift_spark = OpenshiftSpark(
        date_created=date_now,
        report='',
        version_update_task=None
    )

    oshinko_cli = OshinkoCli(
        date_created=date_now,
        report='',
        jenkins_build_task=None,
        oshinko_bin_rel_task=None
    )

    oc_proxy = OcProxy(
        date_created=date_now,
        report='',
        tag_version_task=None
    )

    oshinko_webui = OshinkoWebUi(
        date_created=date_now,
        report='',
        tag_version_task=None
    )

    oshinko_sti = OshinkoWebUi(
        date_created=date_now,
        report='',
        create_release_branch_task=None,
        create_pr_task=None,
        merge_pr_task=None,
        tag_latest_task=None,
        template_release=None
    )

    session_context = SessionContext(
        date_created=date_now,

        openshift_spark=openshift_spark,
        oshinko_cli=oshinko_cli,
        oc_proxy=oc_proxy,
        oshinko_webui=oshinko_webui,
        oshinko_sti=oshinko_sti,
    )

    # Might need to add session contexts to children
    db.session.add(session_context)
    db.session(openshift_spark)
    db.session(oshinko_cli)
    db.session(oc_proxy)
    db.session(oshinko_webui)
    db.session(oshinko_sti)
    db.session.commit()
    return json_response('OC Proxy tag push task started', 200)
