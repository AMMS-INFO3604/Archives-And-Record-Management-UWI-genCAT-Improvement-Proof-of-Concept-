from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_jwt_extended import current_user as jwt_current_user
from flask_jwt_extended import jwt_required

from App.controllers.file import (
    addFile,
    changeFileStatus,
    deleteFile,
    getAllFiles,
    searchFile,
    updateFile,
    viewFile,
)
from App.database import db
from App.models import File

from .index import index_views

file_views = Blueprint("file_views", __name__, template_folder="templates")


@file_views.route("/files", methods=["POST"])
@jwt_required()
def add_file():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    file = addFile(
        boxID=data.get("boxID"),
        fileType=data.get("fileType"),
        locationID=data.get("locationID"),
        loanID=data.get("loanID"),
        description=data.get("description"),
        previousDesignation=data.get("previousDesignation"),
        createdByStaffUserID=data.get("createdByStaffUserID"),
        dateCreated=data.get("dateCreated"),
    )
    if not file:
        return jsonify({"error": "Failed to add file"}), 400
    return jsonify({"message": "File added successfully", "fileID": file.fileID}), 201


@file_views.route("/files/<int:fileID>", methods=["PUT"])
@jwt_required()
def update_file(fileID):
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    file = updateFile(
        fileID=data.get("fileID"),
        boxID=data.get("boxID"),
        locationID=data.get("locationID"),
        loanID=data.get("loanID"),
        fileType=data.get("fileType"),
        description=data.get("description"),
        previousDesignation=data.get("previousDesignation"),
        createdByStaffUserID=data.get("createdByStaffUserID"),
        dateCreated=data.get("dateCreated"),
        status=data.get("status"),
    )
    if not file:
        return jsonify({"error": "File not found"}), 404
    return jsonify({"message": "File updated successfully", "fileID": file.fileID}), 200


@file_views.route("/files/<int:fileID>", methods=["DELETE"])
@jwt_required()
def delete_file(fileID):
    result = deleteFile(fileID)

    if not result:
        return jsonify({"error": "File not found"}), 404
    return jsonify({"message": f"File {fileID} was deleted successfully"}), 200


@file_views.route("/files/<int:fileID>", methods=["GET"])
@jwt_required()
def view_file(fileID):
    file = viewFile(fileID)

    if not file:
        return jsonify({"error": "File not found"}), 404

    return jsonify(
        {
            "fileID": file.fileID,
            "boxID": file.boxID,
            "locationID": file.locationID,
            "loanID": file.loanID,
            "fileType": file.fileType,
            "description": file.description,
            "previousDesignation": file.previousDesignation,
            "createdByStaffUserID": file.createdByStaffUserID,
            "dateCreated": str(file.dateCreated),
            "status": file.status,
        }
    ), 200


@file_views.route("/files", methods=["GET"])
@jwt_required()
def get_all_files():
    files = getAllFiles()
    if not files:
        return jsonify({"message": "No files found"}), 404
    return jsonify(
        [
            {
                "fileID": f.fileID,
                "boxID": f.boxID,
                "fileType": f.fileType,
                "description": f.description,
                "status": f.status,
                "dateCreated": str(f.dateCreated),
            }
            for f in files
        ]
    ), 200


@file_views.route("/files/search", methods=["GET"])
@jwt_required()
def search_file():
    fileID = request.args.get("fileID")
    fileType = request.args.get("fileType")
    locationID = request.args.get("locationID")
    loanID = request.args.get("loanID")
    status = request.args.get("status")

    files = searchFile(
        fileID=fileID,
        fileType=fileType,
        locationID=locationID,
        loanID=loanID,
        status=status,
    )
    if not files:
        return jsonify({"message": "No files found"}), 404
    return jsonify(
        [
            {
                "fileID": f.fileID,
                "fileType": f.fileType,
                "status": f.status,
                "description": f.description,
                "locationID": f.locationID,
            }
            for f in files
        ]
    ), 200


@file_views.route("/files/<int:fileID>/status", methods=["PUT"])
@jwt_required()
def change_file_status(fileID):
    data = request.json
    if not data or "status" not in data:
        return jsonify({"error": "Status is required"}), 400

    file = changeFileStatus(fileID, data["status"])

    if not file:
        return jsonify({"error": "File not found or invalid status"}), 404
    return jsonify(
        {"message": f"File {fileID} status updated successfully", "status": file.status}
    ), 200
