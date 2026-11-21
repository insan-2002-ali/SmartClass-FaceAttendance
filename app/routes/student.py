from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from werkzeug.utils import secure_filename
import os

from models.student_model import StudentModel
from config import Config

student_bp = Blueprint(
    "student",
    __name__
)


@student_bp.route("/students")
def students():

    keyword = request.args.get(
        "keyword",
        ""
    ).strip()

    if keyword:

        students = StudentModel.search_students(
            keyword
        )

    else:

        students = StudentModel.get_all_students()

    total_students = StudentModel.count_students()

    return render_template(
        "admin/students.html",
        students=students,
        keyword=keyword,
        total_students=total_students
    )
@student_bp.route(
    "/students/add",
    methods=["GET", "POST"]
)
def add_student():

    programs = StudentModel.get_programs()
    departments = StudentModel.get_departments()

    if request.method == "POST":

        student_id = request.form["student_id"].strip()
        full_name = request.form["full_name"].strip()
        email = request.form["email"].strip()
        phone = request.form["phone"].strip()
        gender = request.form["gender"]
        date_of_birth = request.form["date_of_birth"]
        program_id = request.form["program_id"]
        department_id = request.form["department_id"]
        password = request.form["password"]
        status = request.form["status"]

        profile_photo = ""

        photo = request.files.get("profile_photo")

        if photo and photo.filename:

            filename = secure_filename(photo.filename)

            photo.save(
                os.path.join(
                    Config.UPLOAD_FOLDER,
                    filename
                )
            )

            profile_photo = filename

        if StudentModel.student_id_exists(student_id):

            flash(
                "Student ID already exists.",
                "danger"
            )

            return render_template(
                "admin/add_student.html",
                programs=programs,
                departments=departments
            )

        if StudentModel.email_exists(email):

            flash(
                "Email already exists.",
                "danger"
            )

            return render_template(
                "admin/add_student.html",
                programs=programs,
                departments=departments
            )

        StudentModel.add_student({

            "student_id": student_id,
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "gender": gender,
            "date_of_birth": date_of_birth,
            "program_id": program_id,
            "department_id": department_id,
            "profile_photo": profile_photo,
            "password": password,
            "status": status

        })

        flash(
            "Student added successfully.",
            "success"
        )

        return redirect(
            url_for("student.students")
        )

    return render_template(
        "admin/add_student.html",
        programs=programs,
        departments=departments
    )
@student_bp.route(
    "/students/edit/<int:id>",
    methods=["GET", "POST"]
)
def edit_student(id):

    student = StudentModel.get_student_by_id(id)

    if not student:

        flash(
            "Student not found.",
            "danger"
        )

        return redirect(
            url_for("student.students")
        )

    programs = StudentModel.get_programs()

    departments = StudentModel.get_departments()

    if request.method == "POST":

        student_id = request.form["student_id"].strip()

        full_name = request.form["full_name"].strip()

        email = request.form["email"].strip()

        phone = request.form["phone"].strip()

        gender = request.form["gender"]

        date_of_birth = request.form["date_of_birth"]

        program_id = request.form["program_id"]

        department_id = request.form["department_id"]

        status = request.form["status"]

        profile_photo = student["profile_photo"]

        photo = request.files.get("profile_photo")

        if photo and photo.filename:

            filename = secure_filename(photo.filename)

            photo.save(
                os.path.join(
                    Config.UPLOAD_FOLDER,
                    filename
                )
            )

            profile_photo = filename

        if StudentModel.student_id_exists_for_update(
            student_id,
            id
        ):

            flash(
                "Student ID already exists.",
                "danger"
            )

            return render_template(
                "admin/edit_student.html",
                student=student,
                programs=programs,
                departments=departments
            )

        if StudentModel.email_exists_for_update(
            email,
            id
        ):

            flash(
                "Email already exists.",
                "danger"
            )

            return render_template(
                "admin/edit_student.html",
                student=student,
                programs=programs,
                departments=departments
            )

        StudentModel.update_student({

            "id": id,
            "student_id": student_id,
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "gender": gender,
            "date_of_birth": date_of_birth,
            "program_id": program_id,
            "department_id": department_id,
            "profile_photo": profile_photo,
            "status": status

        })

        flash(
            "Student updated successfully.",
            "success"
        )

        return redirect(
            url_for("student.students")
        )

    return render_template(
        "admin/edit_student.html",
        student=student,
        programs=programs,
        departments=departments
    )
@student_bp.route(
    "/students/delete/<int:id>"
)
def delete_student(id):

    student = StudentModel.get_student_by_id(id)

    if not student:

        flash(
            "Student not found.",
            "danger"
        )

    else:

        StudentModel.delete_student(id)

        flash(
            "Student deleted successfully.",
            "success"
        )

    return redirect(
        url_for("student.students")
    )
