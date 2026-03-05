from flask import Blueprint, render_template, jsonify, request, send_from_directory, flash, redirect, url_for
from flask_jwt_extended import jwt_required, current_user as jwt_current_user


from.index import index_views

from App.controllers.box import (addBox, updateBox, moveBoxLocation, deleteBox, getBoxByID, getAllBoxes, searchBoxesByLocation)

from App.models import Box
from App import db

box_views = Blueprint('box_views', __name__, template_folder='templates')

@box_views.route('/boxes', methods=['POST'])
@jwt_required()
def add_box():
    data = request.json
    
    if not data:
        return jsonify({'message': 'No input data provided'}), 400
    
    box = addBox(
        bayNo = data.get('bayNo'),
        rowNo = data.get('rowNo'),
        columnNo = data.get('columnNo'),
        barcode = data.get('barcode'),
        locationID = data.get('locationID')
    )
    
    if not box:
        return jsonify({'message': 'Failed to add box'}), 400
    return jsonify({'message': 'Box added successfully', 'box': box}), 201

@box_views.route('/boxes/<int:boxID>', methods=['PUT'])
@jwt_required()
def update_box(boxID):
    data = request.json
    
    if not data:
        return jsonify({'message' : 'No input data was provided'}), 400
    
    box = updateBox(
        boxID = data.get('boxID'),
        bayNo = data.get('bayNo'),
        rowNo = data.get('rowNo'),
        columnNo = data.get('columnNo'),
        barcode = data.get('barcode'),
        locationID = data.get('locationID')
        
    )
    
    if not box:
        return jsonify({'message': 'Failed to update box'}), 400
    return jsonify({'message': 'Box updated successfully', 'box': box}), 200

@box_views.route('/boxes/<int:boxID>/move', methods=['PUT'])
@jwt_required()
def move_box_location(boxID):
    data = request.json
    
    if not data or 'newLocationID' not in data:
        return jsonify({'message' : 'newLocationID is required'}), 400

    box= moveBoxLocation(boxID, data['newLocationID'])
    
    if not box:
        return jsonify({'message': 'Failed to move box'}), 400
    return jsonify({'message': f'Box {boxID} moved successfully',
                    'boxID': box.boxID,
                    'newLocationID': box.locationID}), 200
    
@box_views.route('/boxes/<int:boxID>', methods=['DELETE'])
@jwt_required()
def delete_box(boxID):
    box = deleteBox(boxID)
    
    if not box:
        return jsonify({'message': 'Failed to delete box'}), 400
    return jsonify({'message': f'Box {boxID} deleted successfully'}), 200

@box_views.route('/boxes/<int:boxID>', methods=['GET'])
@jwt_required()
def get_box_by_id(boxID):
    box = getBoxByID(boxID)
    
    if not box:
        return jsonify({'message': f'Box {boxID} not found'}), 404
    return jsonify({'box': box}), 200

@box_views.route('/boxes', methods=['GET'])
@jwt_required()
def get_all_boxes():
    boxes = getAllBoxes()
    
    if not boxes:
        return jsonify({'message': 'No boxes found'}), 404
    return jsonify({'boxes': boxes}), 200

@box_views.route('/boxes/search/<int:locationID>', methods=['GET']) 
@jwt_required()
def search_boxes_by_location(locationID):
    locationID = request.args.get('locationID')
    
    if not locationID:
        return jsonify({'message': 'Location ID is required'}), 400
    
    boxes = searchBoxesByLocation(locationID)
    
    if not boxes:
        return jsonify({'message': f'No boxes found for location with ID {locationID}'}), 404
    return jsonify({'boxes': boxes}), 200

