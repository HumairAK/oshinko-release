from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class SessionContext(db.Model):
    __tablename__ = 'session_context'
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.TIMESTAMP(timezone=True))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    openshift_spark_id = db.Column(db.Integer, db.ForeignKey('openshift_spark.id'))
    oshinko_cli_id = db.Column(db.Integer, db.ForeignKey('oshinko_cli.id'))
    oc_proxy_id = db.Column(db.Integer, db.ForeignKey('oc_proxy.id'))
    oshinko_webui_id = db.Column(db.Integer, db.ForeignKey('oshinko_webui.id'))
    oshinko_sti_id = db.Column(db.Integer, db.ForeignKey('oshinko_sti.id'))
    user = db.relationship("User", uselist=False, back_populates="session_context")

    openshift_spark = db.relationship("OpenshiftSpark", uselist=False, back_populates="session_context")
    oshinko_cli = db.relationship("OshinkoCli", uselist=False, back_populates="session_context")
    oc_proxy = db.relationship("OcProxy", uselist=False, back_populates="session_context")
    oshinko_webui = db.relationship("OshinkoWebUi", uselist=False, back_populates="session_context")
    oshinko_sti = db.relationship("OshinkoSti", uselist=False, back_populates="session_context")


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    session_context = db.relationship("SessionContext", back_populates="user", uselist=False)

    def __repr__(self):
        return '<User %r>' % self.username


class OpenshiftSpark(db.Model):
    __tablename__ = 'openshift_spark'
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.TIMESTAMP(timezone=True))
    report = db.Column(db.LargeBinary(100000))

    version_update_task_id = db.Column(db.Integer, db.ForeignKey('celery_taskmeta.id'))

    session_context = db.relationship("SessionContext", back_populates="openshift_spark", uselist=False)
    version_update_task = db.relationship("CeleryTaskmeta", backref=db.backref("openshift_spark", uselist=False))


class OshinkoCli(db.Model):
    __tablename__ = 'oshinko_cli'
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.TIMESTAMP(timezone=True))
    report = db.Column(db.LargeBinary(100000))

    jenkins_build_task_id = db.Column(db.Integer, db.ForeignKey('celery_taskmeta.id'))
    oshinko_bin_rel_task_id = db.Column(db.Integer, db.ForeignKey('celery_taskmeta.id'))

    session_context = db.relationship("SessionContext", back_populates="oshinko_cli", uselist=False)
    jenkins_build_task = db.relationship("CeleryTaskmeta", backref=db.backref("jenkins_build_oshinko_cli", uselist=False), foreign_keys=[jenkins_build_task_id])
    oshinko_bin_rel_task = db.relationship("CeleryTaskmeta", backref=db.backref("oshinko_bin_rel_oshinko_cli", uselist=False), foreign_keys=[oshinko_bin_rel_task_id])


class OcProxy(db.Model):
    __tablename__ = 'oc_proxy'
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.TIMESTAMP(timezone=True))
    report = db.Column(db.LargeBinary(100000))

    tag_version_task_id = db.Column(db.Integer, db.ForeignKey('celery_taskmeta.id'))

    session_context = db.relationship("SessionContext", back_populates="oc_proxy", uselist=False)
    tag_version_task = db.relationship("CeleryTaskmeta", backref=db.backref("oc_proxy", uselist=False))


class OshinkoWebUi(db.Model):
    __tablename__ = 'oshinko_webui'
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.TIMESTAMP(timezone=True))
    report = db.Column(db.LargeBinary(100000))

    tag_version_task_id = db.Column(db.Integer, db.ForeignKey('celery_taskmeta.id'))

    session_context = db.relationship("SessionContext", back_populates="oshinko_webui", uselist=False)
    tag_version_task = db.relationship("CeleryTaskmeta", backref=db.backref("oshinko_webui", uselist=False))


class OshinkoSti(db.Model):
    __tablename__ = 'oshinko_sti'
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.TIMESTAMP(timezone=True))
    report = db.Column(db.LargeBinary(100000))

    create_release_branch_task_id = db.Column(db.Integer, db.ForeignKey('celery_taskmeta.id'))
    create_pr_task_id = db.Column(db.Integer, db.ForeignKey('celery_taskmeta.id'))
    merge_pr_task_id = db.Column(db.Integer, db.ForeignKey('celery_taskmeta.id'))
    tag_latest_task_id = db.Column(db.Integer, db.ForeignKey('celery_taskmeta.id'))
    template_release_task_id = db.Column(db.Integer, db.ForeignKey('celery_taskmeta.id'))

    session_context = db.relationship("SessionContext", back_populates="oshinko_sti", uselist=False)
    create_release_branch_task = db.relationship("CeleryTaskmeta", backref=db.backref("create_rel_oshinko_sti", uselist=False), foreign_keys=[create_release_branch_task_id])
    create_pr_task = db.relationship("CeleryTaskmeta", backref=db.backref("create_pr_oshinko_sti", uselist=False), foreign_keys=[create_pr_task_id])
    merge_pr_task = db.relationship("CeleryTaskmeta", backref=db.backref("merge_pr_oshinko_sti", uselist=False), foreign_keys=[merge_pr_task_id])
    tag_latest_task = db.relationship("CeleryTaskmeta", backref=db.backref("tag_latest_oshinko_sti", uselist=False), foreign_keys=[tag_latest_task_id])
    template_release = db.relationship("CeleryTaskmeta", backref=db.backref("template_rel_oshinko_sti", uselist=False), foreign_keys=[template_release_task_id])


class CeleryTaskmeta(db.Model):
    __tablename__ = 'celery_taskmeta'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(155), unique=True)
    status = db.Column(db.String(50))
    result = db.Column(db.LargeBinary(20))
    date_done = db.Column(db.TIMESTAMP(timezone=False))
    traceback = db.Column(db.Text)

