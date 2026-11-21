from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash
)

from models.student_model import StudentModel
from services.face_registration import capture_student_faces


face_registration_bp = Blueprint(
    "face_registration",
    __name__
)


@face_registration_bp.route("/face-registration")
def face_registration():

    students = StudentModel.get_all_students()

    return render_template(
        "admin/face_registration.html",
        students=students
    )


@face_registration_bp.route("/face-registration/<int:id>")
def register_student_face(id):

    student = StudentModel.get_student_by_id(id)

    if not student:

        flash(
            "Student not found.",
            "danger"
        )

        return redirect(
            url_for("face_registration.face_registration")
        )

    capture_student_faces(
        student["student_id"]
    )

    flash(
        "Face registration completed successfully.",
        "success"
    )

    return redirect(
        url_for("face_registration.face_registration")
    )