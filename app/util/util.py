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

