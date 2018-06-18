from celery import Celery
from flask import Flask, json


def register_blueprints(flask_app):
    """Register all blueprint modules"""

    from blueprints.mail import mail as mail
    from blueprints.oc_proxy import ocproxy as oc_proxy
    from blueprints.openshift_spark import ospark
    from blueprints.oshinko_cli import oshcli as oshinko_cli
    from blueprints.oshinko_webui import oshwebui as oshinko_webui
    from blueprints.root import home as root
    from blueprints.oshinko_s2i import oshsti as oshinko_s2i
    for bp in [ospark, mail, oc_proxy, oshinko_webui, oshinko_s2i, oshinko_cli, root]:
        flask_app.register_blueprint(bp)


def create_app(register_bp=True):
    app = Flask(__name__)

    backend = 'db+postgresql://userQJC:I5g0wmW3qSub8N6f@localhost:5432/sampledb'
    broker = 'amqp://localhost//'

    if register_bp:
        register_blueprints(app)

    app.config.update(
        CELERY_BROKER_URL=broker,
        CELERY_RESULT_BACKEND=backend,
        CELERY_TRACK_STARTED=True
    )

    app.config.from_json('config.json')

    return app


def create_celery(app):
    celery = Celery(app.import_name, broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    task_base = celery.Task

    class ContextTask(task_base):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return task_base.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery
