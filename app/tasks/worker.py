import tempfile
import subprocess
import jenkins
import os
import magic
import logging as log
from celery_once import QueueOnce
from shutil import rmtree
from flask import json
from ..app import create_app, create_celery
from ..util.git_release import create_release, get_repo
from ..util.watch_builds import watch_build, log as watch_build_logger
from ..util.util import download_file, create_tag, fetch_sti_rel_notes, \
                        fetch_openshift_spark_gh_info, fetch_report

# TODO Tokens are exposed when passed as arguments to tasks, consider using secrets

app = create_app(register_bp=False)
celery = create_celery(app)

celery.conf.ONCE = {
    'backend': app.config['CELERY_ONCE']['BACKEND'],
    'settings': {
        'url': app.config['CELERY_ONCE']['SETTINGS']['URL'],
        'default_timeout': app.config['CELERY_ONCE']['SETTINGS']['DEFAULT_TIMEOUT']
    }
}

# Dockerhub endpoing
DOCKERHUB_ENDPOINT = "https://hub.docker.com/r"
GITHUB_ENDPOINT = "https://github.com"


@celery.task()
def tester():
    return 0


@celery.task(bind=True)
def watch_autobuild(self, tags, repo, token, interval, retries, force):
    watch_build_logger.getLogger('watch_build').setLevel(log.DEBUG)
    log.getLogger('requests').setLevel(log.WARNING)
    try:
        watch_build(repo, token, interval, retries, force, tags)
    except RuntimeError as re:
        # Dockerhub might take a little longer to start the builds
        self.retry(countdown=15, exc=re, max_retries=5)
    return 0


""" OPENSHIFT SPARK """


@celery.task()
def openshift_spark_update(gh_repo_owner, gh_repo_name, gh_user, gh_email, gh_token, version):
    d = tempfile.mkdtemp()
    failed = subprocess.call(['app/util/bash_scripts/repo_ctrl.sh', gh_repo_owner,
                              gh_repo_name, gh_token, d, version, 'openshift-spark',
                              gh_user, gh_email])
    report = fetch_report(d)
    tags_branches = fetch_openshift_spark_gh_info(d)
    rmtree(d, ignore_errors=True)

    tags_branches = json.loads(tags_branches)

    if failed:
        raise RuntimeError('Failed to execute openshift spark version update script.')

    tag, branch = tags_branches['tag'], tags_branches['branch']

    branch_sf, branch_docker_tag = branch, '{}-latest'.format(branch)
    tag_sf, tag_docker_tag = tag, tag

    tags = [{"source_type": "Tag", "sourceref": tag_sf, "docker_tag": tag_docker_tag},
            {"source_type": "Branch", "sourceref": branch_sf, "docker_tag": branch_docker_tag}]
    return tags


""" Oshinko WEBUI """


@celery.task()
def oshinko_webui_version_update(gh_repo_owner, gh_repo_name, gh_user, gh_email, gh_token, version):
    d = tempfile.mkdtemp()
    failed = subprocess.call(['app/util/bash_scripts/repo_ctrl.sh',
                              gh_repo_owner, gh_repo_name, gh_token, d, version,
                              'oshinko-webui', gh_user, gh_email])

    report = fetch_report(d)

    rmtree(d, ignore_errors=True)
    if failed:
        raise RuntimeError('Failed to execute oshinkow_webui version update script.')

    tag_name = create_tag(version)
    tags = [{
        "source_type": "Tag",
        "sourceref": tag_name,
        "docker_tag": tag_name
    }]
    return tags


""" OC PROXY """


@celery.task()
def oc_proxy_version_update(gh_repo_owner, gh_repo_name, gh_user, gh_email, gh_token, version):
    d = tempfile.mkdtemp()
    failed = subprocess.call(['app/util/bash_scripts/repo_ctrl.sh',
                              gh_repo_owner, gh_repo_name, gh_token, d, version,
                              'oc-proxy', gh_user, gh_email])

    report = fetch_report(d)

    rmtree(d, ignore_errors=True)
    if failed:
        raise RuntimeError('Failed to execute oc-proxy version update script.')

    tag_name = create_tag(version)
    tags = [{
        "source_type": "Tag",
        "sourceref": tag_name,
        "docker_tag": tag_name
    }]
    return tags


""" Oshinko CLI """


@celery.task()
def oshinko_cli_jenkins_start_build(host, user, psw, job, ver):
    try:
        server = jenkins.Jenkins(host, username=user, password=psw)
    except jenkins.JenkinsException:
        error_msg = 'Could not login to host [{}] with user [{}].'.format(host, user)
        raise jenkins.JenkinsException(error_msg)
    queue_number = server.build_job(job, parameters=[('VERSION', ver)])
    return 'Started job build, queue number [{}]'.format(queue_number)


# Precondition: filenames for assets match as hardcoded in code, and version parameter exists
@celery.task()
def oshinko_cli_bin_release(job, gh_repo_owner, repo_name, gh_user, gh_email, gh_token):
    log.getLogger('create_release').setLevel(log.INFO)
    log.getLogger('requests').setLevel(log.WARNING)

    build = job['build']
    version = build['parameters']['VERSION']
    artifacts = build['artifacts']

    macosx, linux_amd64, linux_386 = '', '', ''
    for artifact in artifacts:
        filename = os.path.basename(artifact)
        if filename == 'oshinko_v{}_macosx.zip'.format(version):
            macosx = artifact
        elif filename == 'oshinko_v{}_linux_amd64.tar.gz'.format(version):
            linux_amd64 = artifact
        elif filename == 'oshinko_v{}_linux_386.tar.gz'.format(version):
            linux_386 = artifact

    if not all([macosx, linux_386, linux_amd64]):
        raise RuntimeError('Could not find an asset within artifacts from job.')

    # Tmp dir to operate within, removed at end
    tmpdir = tempfile.mkdtemp()

    # Ensure the file is read/write by the creator only
    saved_umask = os.umask(0o077)

    # Download assets from jenkins server
    macosx_file = download_file(artifacts[macosx]['archive'], tmp_dir=tmpdir)
    linux_amd64_file = download_file(artifacts[linux_amd64]['archive'], tmp_dir=tmpdir)
    linux_386_file = download_file(artifacts[linux_386]['archive'], tmp_dir=tmpdir)

    # TODO: Notes should be automated in the future
    with open('release-notes.txt', 'r') as notes_file:
        body = notes_file.read()

    # Create release artifacts
    assets = []
    mime = magic.Magic(mime=True)

    for asset in [macosx_file, linux_386_file, linux_amd64_file]:
        content_type = mime.from_file(asset)
        label = os.path.basename(asset)
        assets.append({'name': asset, 'Content-Type': content_type, 'label': label})

    draft, prerelease = False, False
    target_commitish = 'master'
    tag_name, name = "v{}".format(version), "version {}".format(version)
    repo = get_repo(gh_user, repo_name, gh_token, owner=gh_repo_owner)

    try:
        create_release(repo, tag_name, name, body, draft,
                       prerelease, target_commitish, assets, tmpdir=tmpdir)
    finally:
        os.remove(macosx_file)
        os.remove(linux_amd64_file)
        os.remove(linux_386_file)
        os.umask(saved_umask)
        os.rmdir(tmpdir)

    tags = [{
        "source_type": "Tag",
        "sourceref": tag_name,
        "docker_tag": tag_name
    }]
    return tags


""" Oshinko S2I """


@celery.task()
def oshinko_s2i_create_rel_branch(gh_repo_owner, repo_name, gh_user, gh_email, gh_token, version):
    d = tempfile.mkdtemp()
    failed = subprocess.call(['app/util/bash_scripts/repo_ctrl.sh', '-s 0',
                              gh_repo_owner, repo_name, gh_token, d, version,
                              'oshinko-s2i', gh_user, gh_email])
    report = fetch_report(d)

    rmtree(d, ignore_errors=True)
    if failed:
        raise RuntimeError('Failed to execute oshinko_s2i release branch script.')
    return 0


@celery.task()
def oshinko_s2i_create_pr(gh_repo_owner, gh_repo_name, gh_user, gh_token, version, base_branch):
    repo = get_repo(gh_user, gh_repo_name, gh_token, owner=gh_repo_owner)

    title = '[Release Bot] Release v{}'.format(version)
    body = 'This PR is for a release update to version: {}'.format(version)
    head = 'release{}'.format(version)
    pull = repo.create_pull(title=title, head=head, base=base_branch, body=body)

    return pull


# Precondition: Head branch is named using syntax: releaseXXX where XXX is the version.
@celery.task()
def oshinko_s2i_merge_pr(gh_repo_owner, gh_repo_name, gh_user, gh_token, head_branch,
                         base_branch, sha_commit):

    repo = get_repo(gh_user, gh_repo_name, gh_token, owner=gh_repo_owner)
    pulls = repo.get_pulls(state='open', sort='created', direction='desc',
                           base=base_branch, head='{}:{}'.format(gh_repo_owner, head_branch))
    pull_request = None
    for pull in pulls:
        pull_head = pull.head
        if pull_head.sha == sha_commit and pull_head.user.login == gh_repo_owner:
            pull_request = pull
            break

    if pull_request is None:
        raise RuntimeError('Unable to find PR for {}:{} with head.sha={}'
                           .format(gh_repo_owner, head_branch, sha_commit))

    pr_merge_status = pull_request.merge().merged

    return pr_merge_status


@celery.task()
def oshinko_s2i_tag_latest(gh_repo_owner, gh_repo_name, gh_user, gh_email, gh_token, version):
    print('TAG LATEST STARTED')
    d = tempfile.mkdtemp()
    failed = subprocess.call(['app/util/bash_scripts/repo_ctrl.sh', '-s 1',
                              gh_repo_owner, gh_repo_name, gh_token, d, version,
                              'oshinko-s2i', gh_user, gh_email])
    report = fetch_report(d)

    rmtree(d, ignore_errors=True)
    if failed:
        raise RuntimeError('Failed to execute oshinko_s2i tag latest.')

    tag_name = create_tag(version)
    tags = [{
        "source_type": "Tag",
        "sourceref": tag_name,
        "docker_tag": tag_name
    }]
    return tags


@celery.task()
def oshinko_s2i_template_release(gh_repo_owner, gh_repo_name, gh_user,
                                 gh_token, version, dh_repos, oshinko_gh_repo_path):
    log.getLogger('create_release').setLevel(log.INFO)

    body = fetch_sti_rel_notes()

    # https://github.com/radanalyticsio/oshinko-cli/releases/tag/
    body = body.replace('<<<OSHINKO_VERSION>>>', version)
    oshinko_cli_ln = '{}/{}/releases/tag/v{}'.format(GITHUB_ENDPOINT, oshinko_gh_repo_path, version)

    body = body.replace('<<<CLI_LINK>>>', '[here]({})'.format(oshinko_cli_ln))

    d_repos_ordered = dh_repos['sti_scala'], dh_repos['sti_java'], dh_repos['sti_spark']
    scala_ln, java_ln, pyspark_ln = (
        '{}/{}/'.format(DOCKERHUB_ENDPOINT, sti)
        for sti in d_repos_ordered)

    body = body.replace('<<<PYSPARK_LINK>>>', '[here]({})'.format(pyspark_ln))
    body = body.replace('<<<JAVA_SPARK_LINK>>>', '[here]({})'.format(java_ln))
    body = body.replace('<<<SCALA_SPARK_LINK>>>', '[here]({})'.format(scala_ln))

    draft, prerelease = False, False
    target_commitish = 'master'
    tag_name, name = "v{}".format(version), "version {}".format(version)
    gh_repo = get_repo(gh_user, gh_repo_name, gh_token, owner=gh_repo_owner)

    create_release(gh_repo, tag_name, name, body, draft, prerelease, target_commitish)

    return 0

