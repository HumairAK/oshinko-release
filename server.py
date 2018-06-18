#!/usr/bin/python2

from app.app import create_app

if __name__ == '__main__':
    app = create_app()
    app.run(host=app.config['DEFAULT']['IP'], port=app.config['DEFAULT']['PORT'])