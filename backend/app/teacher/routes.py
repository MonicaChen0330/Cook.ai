from flask import Blueprint, jsonify

teacher_bp = Blueprint('teacher', __name__, url_prefix='/api/teacher')

@teacher_bp.route('/materials', methods=['POST'])
def create_course_material():
    return jsonify({"message": "This will generate course materials."})