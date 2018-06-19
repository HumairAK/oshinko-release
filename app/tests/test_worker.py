from ..util.util import fetch_dh_info, fetch_gh_info
from ..tasks import worker
from mock import MagicMock


def test_oshinko_s2i_template_release(client):
    app = client.application

    sti_scala, sti_scala_token = fetch_dh_info(app, 'OSHINKO_S2I_SCALA')
    sti_java, sti_java_token = fetch_dh_info(app, 'OSHINKO_S2I_JAVA')
    sti_pyspark, sti_pyspark_token = fetch_dh_info(app, 'OSHINKO_S2I_PYSPARK')
    dh_repos = {"sti_scala": sti_scala, "sti_java": sti_java, "sti_spark": sti_pyspark}
    gh_repo_owner, gh_repo_name = app.config['UPSTREAM_REPOS']['OSHINKO_S2I'].split('/')
    gh_user, gh_email, gh_token = fetch_gh_info(app)
    oshinko_gh_repo_path = app.config['UPSTREAM_REPOS']['OSHINKO_CLI']

    with open('app/tests/resources/sti-rel-notes-pre-parse.txt', 'r') as notes_file:
        notes_to_parse = notes_file.read()

    with open('app/tests/resources/sti-rel-notes-expected.txt', 'r') as notes_file:
        notes_expected = notes_file.read()

    worker.get_repo = MagicMock(return_value='Mock Repository')
    worker.create_release = MagicMock(return_value=0)
    worker.fetch_sti_rel_notes = MagicMock(return_value=notes_to_parse)

    worker.oshinko_s2i_template_release(gh_repo_owner, gh_repo_name, gh_user,
                                        gh_token, '0.5.2', dh_repos, oshinko_gh_repo_path)

    worker.get_repo.assert_called_with(gh_user, gh_repo_name, gh_token, owner=gh_repo_owner)
    worker.create_release.assert_called_with('Mock Repository', 'v0.5.2',
                                             'version 0.5.2', notes_expected,
                                             False, False, 'master')

