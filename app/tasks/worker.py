import tempfile
import subprocess
import jenkins
import os
import magic
import logging as log
from shutil import rmtree

from github import GithubException

from ..app import create_app, create_celery
from ..util.util import download_file, create_tag
from ..util.git_release import create_release, get_repo
from ..util.watch_builds import watch_build

# TODO Tokens are exposed when passed as arguments to tasks, consider using secrets

app = create_app(register_bp=False)
celery = create_celery(app)


@celery.task(bind=True)
def watch_autobuild(self, tags, repo, token, interval, retries, force):
    print('WATCHING BUILD for tag {}'.format(tags))
    log.getLogger('watch_build').setLevel(log.DEBUG)
    log.getLogger('requests').setLevel(log.WARNING)
    try:
        watch_build(repo, token, interval, retries, force, tags)
    except RuntimeError as re:
        # Dockerhub might take a little longer to start the builds
        self.retry(countdown=10, exc=re, max_retries=3)
    return 0


""" OPENSHIFT SPARK """


@celery.task()
def openshift_spark_update(user, repo, token, version):
    d = tempfile.mkdtemp()
    print(user, repo, token, version, d)
    return subprocess.call(['app/util/bash_scripts/repo_ctrl.sh',
                            user, repo, token, d, version, 'openshift-spark'])


""" Oshinko WEBUI """


@celery.task()
def oshinko_webui_version_update(user, repo, token, version):
    d = tempfile.mkdtemp()
    print(user, repo, token, version, d)
    failed = subprocess.call(['app/util/bash_scripts/repo_ctrl.sh',
                              user, repo, token, d, version, 'oshinko-webui'])

    if failed:
        rmtree(d, ignore_errors=True)
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
def oc_proxy_version_update(user, repo, token, version):
    d = tempfile.mkdtemp()
    print(user, repo, token, version, d)
    failed = subprocess.call(['app/util/bash_scripts/repo_ctrl.sh',
                              user, repo, token, d, version, 'oc-proxy'])

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
def oshinko_cli_bin_release(job, user, repo_name, token):
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
    repo = get_repo(user, repo_name, token)

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
def oshinko_s2i_create_release_branch(user, repo_name, token, version, author, email):
    d = tempfile.mkdtemp()
    print(user, repo_name, token, version, d)
    failed = subprocess.call(['app/util/bash_scripts/repo_ctrl.sh', '-s 0',
                              user, repo_name, token, d, version, 'oshinko-s2i', author, email])
    rmtree(d, ignore_errors=True)
    if failed:
        raise RuntimeError('Failed to execute oshinko_s2i release branch script.')
    return 0


@celery.task()
def oshinko_s2i_create_pr(user, repo_name, token, version, base):
    repo = get_repo(user, repo_name, token)

    title = '[Release Bot] Release v{}'.format(version)
    body = 'This PR is for a release update to version: {}'.format(version)
    head = 'release{}'.format(version)
    pull = repo.create_pull(title=title, head=head, base=base, body=body)

    return pull


# Precondition: Head branch is named using syntax: releaseXXX where XXX is the version.
@celery.task()
def oshinko_s2i_merge_pr(user, repo_name, token, base_branch, author, head, sha, version):
    print('MERGE PR STARTED')

    repo = get_repo(user, repo_name, token)
    pulls = repo.get_pulls(state='open', sort='created', direction='desc',
                           base=base_branch, head='{}:{}'.format(author, head))
    pull_request = None
    for pull in pulls:
        pull_head = pull.head
        if pull_head.sha == sha and pull_head.user.login == author:
            pull_request = pull
            break

    if pull_request is None:
        raise RuntimeError('Unable to find PR for {}:{} with head.sha={}'.format(author, head, sha))

    pr_merge_status = pull_request.merge().merged

    return pr_merge_status


@celery.task()
def oshinko_s2i_tag_latest(user, repo_name, token, version,  author, email):
    print('TAG LATEST STARTED')
    d = tempfile.mkdtemp()
    print(user, repo_name, token, version, d)
    failed = subprocess.call(['app/util/bash_scripts/repo_ctrl.sh', '-s 1',
                              user, repo_name, token, d, version, 'oshinko-s2i', author, email])

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
def oshinko_s2i_template_release(user, repo_name, token, version):
    # Ensure the file is read/write by the creator only

    # TODO: Notes should be automated in the future
    with open('sti-release-notes.txt', 'r') as notes_file:
        body = notes_file.read()

    body = body.replace('<<<OSHINKO_VERSION>>>', version)
    body = body.replace('<<<CLI_LINK>>>',
                        'https://github.com/radanalyticsio/oshinko-cli/releases/tag/v{}'
                        .format(version))
    draft, prerelease = False, False
    target_commitish = 'master'
    tag_name, name = "v{}".format(version), "version {}".format(version)
    repo = get_repo(user, repo_name, token)

    create_release(repo, tag_name, name, body, draft, prerelease, target_commitish)

    return 0

