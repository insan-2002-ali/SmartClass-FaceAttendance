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

from models.teacher_model import TeacherModel
from config import Config

teacher_bp = Blueprint(
    "teacher",
    __name__
)


@teacher_bp.route("/teachers")
def teachers():

    keyword = request.args.get(
        "keyword",
        ""
    ).strip()

    department_id = request.args.get(
        "department_id",
        ""
    ).strip()

    if keyword or department_id:

        teachers = TeacherModel.search_teachers(
            keyword,
            department_id
        )

    else:

        teachers = TeacherModel.get_all_teachers()

    departments = TeacherModel.get_department_teacher_count()

    total_teachers = TeacherModel.count_teachers()

    return render_template(
        "admin/teachers.html",
        teachers=teachers,
        departments=departments,
        keyword=keyword,
        department_id=department_id,
        total_teachers=total_teachers
    )


@teacher_bp.route(
    "/teachers/add",
    methods=["GET", "POST"]
)
def add_teacher():

    departments = TeacherModel.get_departments()

    if request.method == "POST":

        teacher_id = request.form["teacher_id"].strip()
        full_name = request.form["full_name"].strip()
        email = request.form["email"].strip()
        phone = request.form["phone"].strip()
        gender = request.form["gender"]
        designation = request.form["designation"].strip()
        department_id = request.form["department_id"]
        password = request.form["password"]
        status = request.form["status"]

        profile_photo = ""

        photo = request.files.get(
            "profile_photo"
        )

        if photo and photo.filename:

            filename = secure_filename(
                photo.filename
            )

            photo.save(
                os.path.join(
                    Config.UPLOAD_FOLDER,
                    filename
                )
            )

            profile_photo = filename

        if TeacherModel.teacher_id_exists(
            teacher_id
        ):

            flash(
                "Teacher ID already exists.",
                "danger"
            )

            return render_template(
                "admin/add_teacher.html",
                departments=departments
            )

        if TeacherModel.email_exists(
            email
        ):

            flash(
                "Email already exists.",
                "danger"
            )

            return render_template(
                "admin/add_teacher.html",
                departments=departments
            )

        TeacherModel.add_teacher({

            "teacher_id": teacher_id,
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "gender": gender,
            "designation": designation,
            "department_id": department_id,
            "profile_photo": profile_photo,
            "password": password,
            "status": status

        })

        flash(
            "Teacher added successfully.",
            "success"
        )

        return redirect(
            url_for("teacher.teachers")
        )

    return render_template(
        "admin/add_teacher.html",
        departments=departments
    )
@teacher_bp.route(
    "/teachers/edit/<int:id>",
    methods=["GET", "POST"]
)
def edit_teacher(id):

    teacher = TeacherModel.get_teacher_by_id(id)

    if not teacher:

        flash(
            "Teacher not found.",
            "danger"
        )

        return redirect(
            url_for("teacher.teachers")
        )

    departments = TeacherModel.get_departments()

    if request.method == "POST":

        teacher_id = request.form["teacher_id"].strip()
        full_name = request.form["full_name"].strip()
        email = request.form["email"].strip()
        phone = request.form["phone"].strip()
        gender = request.form["gender"]
        designation = request.form["designation"].strip()
        department_id = request.form["department_id"]
        status = request.form["status"]

        profile_photo = teacher["profile_photo"]

        photo = request.files.get(
            "profile_photo"
        )

        if photo and photo.filename:

            filename = secure_filename(
                photo.filename
            )

            photo.save(
                os.path.join(
                    Config.UPLOAD_FOLDER,
                    filename
                )
            )

            profile_photo = filename

        if TeacherModel.teacher_id_exists_for_update(
            teacher_id,
            id
        ):

            flash(
                "Teacher ID already exists.",
                "danger"
            )

            return render_template(
                "admin/edit_teacher.html",
                teacher=teacher,
                departments=departments
            )

        if TeacherModel.email_exists_for_update(
            email,
            id
        ):

            flash(
                "Email already exists.",
                "danger"
            )

            return render_template(
                "admin/edit_teacher.html",
                teacher=teacher,
                departments=departments
            )

        TeacherModel.update_teacher({

            "id": id,
            "teacher_id": teacher_id,
            "full_name": full_name,
            "email": email,
            "phone": phone,
            "gender": gender,
            "designation": designation,
            "department_id": department_id,
            "profile_photo": profile_photo,
            "status": status

        })

        flash(
            "Teacher updated successfully.",
            "success"
        )

        return redirect(
            url_for("teacher.teachers")
        )

    return render_template(
        "admin/edit_teacher.html",
        teacher=teacher,
        departments=departments
    )
@teacher_bp.route("/teachers/delete/<int:id>")
def delete_teacher(id):

    teacher = TeacherModel.get_teacher_by_id(id)

    if not teacher:

        flash(
            "Teacher not found.",
            "danger"
        )

        return redirect(
            url_for("teacher.teachers")
        )

    TeacherModel.delete_teacher(id)

    flash(
        "Teacher deleted successfully.",
        "success"
    )

    return redirect(
        url_for("teacher.teachers")
    )


@teacher_bp.route("/teachers/search")
def search_teacher():

    keyword = request.args.get(
        "keyword",
        ""
    ).strip()

    department_id = request.args.get(
        "department_id",
        ""
    ).strip()

    teachers = TeacherModel.search_teachers(
        keyword,
        department_id
    )

    departments = TeacherModel.get_department_teacher_count()

    total_teachers = len(teachers)

    return render_template(
        "admin/teachers.html",
        teachers=teachers,
        departments=departments,
        keyword=keyword,
        department_id=department_id,
        total_teachers=total_teachers
    )