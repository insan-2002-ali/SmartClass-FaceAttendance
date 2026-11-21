from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from models.student_enrollment_model import (
    StudentEnrollmentModel
)

student_enrollment_bp = Blueprint(
    "student_enrollment",
    __name__
)
@student_enrollment_bp.route("/student-enrollments")
def student_enrollments():

    keyword = request.args.get(
        "keyword",
        ""
    ).strip()

    if keyword:

        enrollments = StudentEnrollmentModel.search_enrollments(
            keyword
        )

    else:

        enrollments = StudentEnrollmentModel.get_all_enrollments()

    return render_template(
        "admin/student_enrollments.html",
        enrollments=enrollments,
        keyword=keyword
    )
@student_enrollment_bp.route(
    "/student-enrollments/add",
    methods=["GET","POST"]
)
def add_student_enrollment():

    students = StudentEnrollmentModel.get_all_students()

    assignments = StudentEnrollmentModel.get_all_teacher_assignments()

    if request.method == "POST":

        student_id = request.form["student_id"]

        teacher_assignment_id = request.form[
            "teacher_assignment_id"
        ]

        status = request.form["status"]

        if StudentEnrollmentModel.enrollment_exists(
            student_id,
            teacher_assignment_id
        ):

            flash(
                "This student is already enrolled.",
                "danger"
            )

            return render_template(
                "admin/add_student_enrollment.html",
                students=students,
                assignments=assignments
            )

        StudentEnrollmentModel.add_enrollment({

            "student_id":student_id,

            "teacher_assignment_id":teacher_assignment_id,

            "status":status

        })

        flash(
            "Student enrolled successfully.",
            "success"
        )

        return redirect(
            url_for(
                "student_enrollment.student_enrollments"
            )
        )

    return render_template(
        "admin/add_student_enrollment.html",
        students=students,
        assignments=assignments
    )
@student_enrollment_bp.route(
    "/student-enrollments/edit/<int:id>",
    methods=["GET","POST"]
)
def edit_student_enrollment(id):

    enrollment = StudentEnrollmentModel.get_enrollment_by_id(
        id
    )

    if not enrollment:

        flash(
            "Enrollment not found.",
            "danger"
        )

        return redirect(
            url_for(
                "student_enrollment.student_enrollments"
            )
        )

    students = StudentEnrollmentModel.get_all_students()

    assignments = StudentEnrollmentModel.get_all_teacher_assignments()

    if request.method == "POST":

        student_id = request.form["student_id"]

        teacher_assignment_id = request.form[
            "teacher_assignment_id"
        ]

        status = request.form["status"]

        if StudentEnrollmentModel.enrollment_exists_for_update(

            student_id,

            teacher_assignment_id,

            id

        ):

            flash(
                "This enrollment already exists.",
                "danger"
            )

            return render_template(

                "admin/edit_student_enrollment.html",

                enrollment=enrollment,

                students=students,

                assignments=assignments

            )

        StudentEnrollmentModel.update_enrollment({

            "id":id,

            "student_id":student_id,

            "teacher_assignment_id":teacher_assignment_id,

            "status":status

        })

        flash(
            "Enrollment updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "student_enrollment.student_enrollments"
            )
        )

    return render_template(

        "admin/edit_student_enrollment.html",

        enrollment=enrollment,

        students=students,

        assignments=assignments

    )
@student_enrollment_bp.route(
    "/student-enrollments/delete/<int:id>"
)
def delete_student_enrollment(id):

    enrollment = StudentEnrollmentModel.get_enrollment_by_id(
        id
    )

    if not enrollment:

        flash(
            "Enrollment not found.",
            "danger"
        )

    else:

        StudentEnrollmentModel.delete_enrollment(id)

        flash(
            "Enrollment deleted successfully.",
            "success"
        )

    return redirect(
        url_for(
            "student_enrollment.student_enrollments"
        )
    )
