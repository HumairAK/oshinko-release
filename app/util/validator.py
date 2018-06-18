from functools import wraps
from flask import request, jsonify
from cerberus import Validator


def validate_schema(schema, allow_unknown=False):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kw):
            v = Validator(schema)
            v.allow_unknown = allow_unknown

            if request.json is None:
                return jsonify({"Status": "Error", "msg": "No payload found."}), 422

            is_valid = v.validate(request.json, schema)
            msg = "payload must be a valid json"

            if not is_valid:
                return jsonify({"Status": "Error", "msg": msg, "validation_error": v.errors}), 400

            return f(*args, **kw)
        return wrapper
    return decorator
