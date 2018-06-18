import requests
from flask import Blueprint, Response, json, current_app as app, request
from celery import chain, group
from ..util.post_schemas import schemas
from ..util.validator import validate_schema
from ..util.util import json_response, get_repo
from ..tasks import worker

oshsti = Blueprint('oshinko_s2i', __name__, url_prefix='/oshinko_s2i')

# CI Contexts
CONTEXTS = ['continuous-integration/travis-ci/pr', 'jenkins-ci/oshinko-s2i']

# Branch to merge release changes to
BASE_BRANCH = 'master-copy'


# Docker watch configs:
INTERVAL = 150
RETRY_COUNT = 500


# Launch script that will commit changes to a branch
# The task will chain into a new task that creates the PR
@oshsti.route("/create/release_branch/<version>", methods=['POST'])
def create_release_branch(version):
    # Update the image.*.yaml files with the change-yaml.sh script
    # Regenerate the *-build directories with make-build-dirs.sh
    # Commit the changes on a releaseXXX branch and make a PR
    oshinko_s2i = app.config['UPSTREAM_REPOS']['OSHINKO_S2I']
    user, repo_name = oshinko_s2i['REPO'].split('/')
    token = oshinko_s2i['TOKEN']
    bot_name = app.config['META']['BOT_NAME']
    bot_email = app.config['META']['BOT_EMAIL']

    # Jenkins/Travis tests run on PR as checks
    create_pull = worker.oshinko_s2i_create_pr.si(user, repo_name, token, version, BASE_BRANCH)

    worker.oshinko_s2i_create_release_branch.apply_async((user, repo_name, token,
                                                          version, bot_name,
                                                          bot_email), link=create_pull)

    return json_response('Release branch task is queued.', 200)


@oshsti.route("/merge/pr", methods=['POST'])
@validate_schema(schemas['oshinko_s2i']['merge_pr'], allow_unknown=True)
def merge_pr():
    """ This endpiont listens for status events on commit's started by the automation server.
    If the endpoint is hit, all contexts/builds being watched for searched against the statuses for
    the head commit attached to the event. If all contexts/builds are successful, a workflow task
    is queued.
    The workflow consists of Merging the PR -> Creating Tag -> Watching autobuilds -> Release.
    If any task within the work flow fails, the workflow is interrupted and does not complete.
    """
    context_header, event = 'X-GitHub-Event', 'status'
    headers = request.headers
    if context_header not in headers and event != headers[context_header]:
        return json_response('Non status event received', 422)
    data = request.data
    data_dict = json.loads(data)

    context = data_dict['context']
    commit = data_dict['commit']
    state = data_dict['state']
    author = commit['commit']['author']['name']
    bot_name = app.config['META']['BOT_NAME']
    bot_email = app.config['META']['BOT_EMAIL']
    sha = commit['sha']

    # Only concerned with events authored by the automation system
    if author != bot_name:
        msg = 'Event not associated with author {}. No merge initiated.'.format(bot_name),
        return json_response(msg, 200)

    # Only concerned with builds that are successful
    if state != 'success':
        msg = 'Event is not in success state. No merge initiated.',
        return json_response(msg, 200)

    # Get all statuses pertaining to this head commit:
    status_endpoint = data_dict['repository']['statuses_url'].format(sha=sha)
    statuses = requests.get(status_endpoint).json()
    statuses = filter(lambda s: s['state'] == 'success', statuses)
    if not statuses:
        return json_response('No success events found within statuses_url.', 400)

    # If a context/build is still pending, merge is not handled
    contexts = CONTEXTS[:]
    i = 0
    while contexts and i < len(statuses):
        status = statuses[i]
        if status['context'] in contexts and status['state'] == 'success':
            contexts.remove(status['context'])
        i += 1
    if contexts:
        msg = 'One of the contexts is not in success state. No merge initiated.'
        return json_response(msg, 200)

    # Only concerned with events associated with one branch (the release branch)
    branches = data_dict['branches']
    if len(branches) != 1:
        msg = '{} branch(es) associated with this event (There should be only one). ' \
              'No merge initiated.'.format(len(branches))
        return json_response(msg, 200)

    # Create Workflow
    head_name = branches[0]['name']
    oshinko_s2i = app.config['UPSTREAM_REPOS']['OSHINKO_S2I']
    user, repo_name = oshinko_s2i['REPO'].split('/')
    token = oshinko_s2i['TOKEN']
    version = head_name.replace('release', '')

    sti_scala = app.config['DOCKERHUB_REPOS']['OSHINKO_S2I_SCALA']
    sti_java = app.config['DOCKERHUB_REPOS']['OSHINKO_S2I_JAVA']
    sti_spark = app.config['DOCKERHUB_REPOS']['OSHINKO_S2I_PYSPARK']

    merge_pull_request = worker.oshinko_s2i_merge_pr.si(user, repo_name, token,
                                                        BASE_BRANCH, bot_name,
                                                        head_name, sha, version)
    sti_tag_latest = worker.oshinko_s2i_tag_latest.si(user, repo_name, token,
                                                      version, bot_name, bot_email)

    # Group watchbuild tasks, to run in parallel
    watch_scala_build = worker.watch_autobuild.s(sti_scala['REPO'], sti_scala['TOKEN'],
                                                 INTERVAL, RETRY_COUNT, False)
    watch_java_build = worker.watch_autobuild.s(sti_java['REPO'], sti_java['TOKEN'],
                                                INTERVAL, RETRY_COUNT, False)
    watch_sti_spark = worker.watch_autobuild.s(sti_spark['REPO'], sti_spark['TOKEN'],
                                               INTERVAL, RETRY_COUNT, False)

    build_tasks = group(watch_java_build, watch_scala_build, watch_sti_spark)
    sti_template_rel = worker.oshinko_s2i_template_release.si(user, repo_name, token, version)

    # Queue Workflow
    workflow = (merge_pull_request | sti_tag_latest | build_tasks | sti_template_rel)
    workflow.delay()

    return json_response('Merge task started.', 200)



