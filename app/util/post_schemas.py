schemas = {
    'openshift_spark': {
        'update': {
            'token': {'type': 'string', 'required': True}
        }
    },
    'oshinko_cli': {
        'start_build': {
            'jenkins_host': {'type': 'string', 'required': True},
            'jenkins_user': {'type': 'string', 'required': True},
            'jenkins_psw': {'type': 'string', 'required': True},
            'jenkins_job': {'type': 'string', 'required': True},
            'oshinko_ver': {'type': 'string', 'required': True, 'regex': r'^[\d\.]+$'}
        },
        'build_finish': {
            "url": {'type': 'string', 'required': True},
            "display_name": {'type': 'string', 'required': True},
            "name": {'type': 'string', 'required': True},
            'build': {
                'type': 'dict',
                'required': True,
                'schema': {
                    "phase": {'type': 'string', 'required': True},
                    "parameters": {
                        'type': 'dict',
                        'required': True,
                        'schema': {
                            'VERSION': {'type': 'string', 'required': True}
                        }
                    },
                    "queue_id": {'type': 'integer', 'required': True}
                }
            }
        }
    },
    'oshinko_s2i': {
        'merge_pr': {
            'commit': {'type': 'dict', 'required': True},
            'sha': {'type': 'string', 'required': True},
            'state': {'type': 'string', 'required': True},
            'context': {'type': 'string', 'required': True}
        }
    }
}
