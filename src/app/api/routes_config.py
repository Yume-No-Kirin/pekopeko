"""
Config endpoint (sync, read-only, ADI-010 SS4): projects the already-loaded
PekopekoConfig as JSON. No write endpoint - out of TASK-007's scope.
"""
from flask import Blueprint, jsonify

from ..config import load_config
from . import serialization

config_bp = Blueprint("config", __name__)


@config_bp.route("/config", methods=["GET"])
def get_config():
    cfg = load_config()
    return jsonify(serialization.config_to_dict(cfg)), 200
