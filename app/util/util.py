import os
import requests
from flask import Response, json
from github import Github, BadCredentialsException
import logging as log


def download_file(url, tmp_dir):
    base_file = os.path.basename(url)
    local_filename = os.path.join(tmp_dir, base_file)

    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    if r.status_code == 403:
        raise requests.HTTPError('Unable to access file on jenkins instance at url: ' + url)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                # filter out keep-alive new chunks
                f.write(chunk)
    return local_filename


def get_repo(user, repo_name, token):
    github = Github(user, token)
    try:
        repo = github.get_user(user).get_repo(repo_name)
    except BadCredentialsException:
        error_msg = 'Bad Github credentials. Ensure a valid user and password/token are provided.'
        log.error(error_msg)
        raise BadCredentialsException
    return repo


def create_tag(version):
    return 'v{}'.format(version)


def json_response(message, code):
    status = 'OK' if code == 200 else 'ERROR'
    payload = json.dumps({'Status': status, 'msg': message})
    return Response(payload, status=code, mimetype="application/json")


def fetch_gh_info(app):
    gh_user = app.config['GH_USER_INFO']['GH_USER']
    gh_email = app.config['GH_USER_INFO']['GH_EMAIL']
    gh_token = app.config['GH_USER_INFO']['GH_AUTH_TOKEN']
    return gh_user, gh_email, gh_token


def fetch_dh_info(app, repo):
    dockerhub_repo = app.config['DOCKERHUB_REPOS'][repo]['REPO']
    dockerhub_token = app.config['DOCKERHUB_REPOS'][repo]['TOKEN']
    return dockerhub_repo, dockerhub_token


def fetch_sti_rel_notes():
    with open('sti-release-notes.txt', 'r') as notes_file:
        notes = notes_file.read()
    return notes


def fetch_openshift_spark_gh_info(tmpdir):
    path = os.path.join(tmpdir, 'project_report', 'gh_info.json')
    with open(path, 'r') as f:
        data = f.read()
    return data


def fetch_report(tmpdir):
    path = os.path.join(tmpdir, 'project_report', 'outfile.txt')
    with open(path, 'r') as f:
        data = f.read()
    return data