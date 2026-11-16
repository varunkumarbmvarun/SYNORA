from typing import Any, Optional
from flask import jsonify

def success_response(data: Any = None, message: str = "Success", status_code: int = 200):
    return jsonify({
        "success": True,
        "data": data,
        "message": message
    }), status_code

def error_response(message: str, code: str = "ERROR", details: Any = None, status_code: int = 400):
    return jsonify({
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details
        }
    }), status_code
