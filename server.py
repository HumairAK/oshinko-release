#!/usr/bin/python2

from app.app import create_app
from app.models.models import db

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all(app=app)
    app.run(host=app.config['DEFAULT']['IP'], port=app.config['DEFAULT']['PORT'])