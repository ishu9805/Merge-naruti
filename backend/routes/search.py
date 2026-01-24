from flask import Blueprint, request, jsonify
from backend.db import global_collection, user_collection
from backend.search_engine import run_search

search_bp = Blueprint("search", __name__)


@search_bp.route("/api/search/global")
def global_search():
    q = request.args.get("q", "")
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))

    return jsonify(run_search(global_collection, q, page, limit))


@search_bp.route("/api/search/user")
def user_search():
    q = request.args.get("q", "")
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))

    return jsonify(run_search(user_collection, q, page, limit))
