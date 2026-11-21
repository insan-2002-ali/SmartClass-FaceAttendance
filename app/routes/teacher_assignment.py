from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from models.teacher_assignment_model import (
    TeacherAssignmentModel
)

teacher_assignment_bp = Blueprint(
    "teacher_assignment",
    __name__
)


@teacher_assignment_bp.route("/teacher-assignments")
def teacher_assignments():

    keyword = request.args.get(
        "keyword",
        ""
    ).strip()

    teacher_id = request.args.get(
        "teacher_id",
        ""
    ).strip()

    department_id = request.args.get(
        "department_id",
        ""
    ).strip()

    semester = request.args.get(
        "semester",
        ""
    ).strip()

    admission_year_id = request.args.get(
        "admission_year_id",
        ""
    ).strip()

    if keyword:

        assignments = TeacherAssignmentModel.search_assignments(
            keyword
        )

    elif (
        teacher_id
        or department_id
        or semester
        or admission_year_id
    ):

        assignments = TeacherAssignmentModel.filter_assignments(
            teacher_id,
            department_id,
            semester,
            admission_year_id
        )

    else:

        assignments = TeacherAssignmentModel.get_all_assignments()

    teachers = TeacherAssignmentModel.get_teachers()

    departments = TeacherAssignmentModel.get_departments()

    admission_years = TeacherAssignmentModel.get_admission_years()

    return render_template(
        "admin/teacher_assignments.html",
        assignments=assignments,
        teachers=teachers,
        departments=departments,
        admission_years=admission_years,
        keyword=keyword,
        teacher_id=teacher_id,
        department_id=department_id,
        semester=semester,
        admission_year_id=admission_year_id
    )


@teacher_assignment_bp.route(
    "/teacher-assignments/add",
    methods=["GET", "POST"]
)
def add_teacher_assignment():

    teachers = TeacherAssignmentModel.get_teachers()
    departments = TeacherAssignmentModel.get_departments()
    subjects = TeacherAssignmentModel.get_subjects()
    admission_years = TeacherAssignmentModel.get_admission_years()

    if request.method == "POST":

        data = {
            "teacher_id": request.form["teacher_id"],
            "department_id": request.form["department_id"],
            "subject_id": request.form["subject_id"],
            "admission_year_id": request.form["admission_year_id"],
            "semester": request.form["semester"],
            "section": request.form["section"],
            "academic_year": request.form["academic_year"],
            "status": request.form["status"]
        }

        if TeacherAssignmentModel.assignment_exists(data):

            flash(
                "This assignment already exists.",
                "danger"
            )

            return render_template(
                "admin/add_teacher_assignment.html",
                teachers=teachers,
                departments=departments,
                subjects=subjects,
                admission_years=admission_years
            )

        TeacherAssignmentModel.add_assignment(data)

        flash(
            "Teacher assignment added successfully.",
            "success"
        )

        return redirect(
            url_for("teacher_assignment.teacher_assignments")
        )

    return render_template(
        "admin/add_teacher_assignment.html",
        teachers=teachers,
        departments=departments,
        subjects=subjects,
        admission_years=admission_years
    )


@teacher_assignment_bp.route(
    "/teacher-assignments/edit/<int:id>",
    methods=["GET", "POST"]
)
def edit_teacher_assignment(id):

    assignment = TeacherAssignmentModel.get_assignment_by_id(id)

    if not assignment:

        flash(
            "Assignment not found.",
            "danger"
        )

        return redirect(
            url_for("teacher_assignment.teacher_assignments")
        )

    teachers = TeacherAssignmentModel.get_teachers()
    departments = TeacherAssignmentModel.get_departments()
    subjects = TeacherAssignmentModel.get_subjects()
    admission_years = TeacherAssignmentModel.get_admission_years()

    if request.method == "POST":

        data = {
            "id": id,
            "teacher_id": request.form["teacher_id"],
            "department_id": request.form["department_id"],
            "subject_id": request.form["subject_id"],
            "admission_year_id": request.form["admission_year_id"],
            "semester": request.form["semester"],
            "section": request.form["section"],
            "academic_year": request.form["academic_year"],
            "status": request.form["status"]
        }

        TeacherAssignmentModel.update_assignment(data)

        flash(
            "Teacher assignment updated successfully.",
            "success"
        )

        return redirect(
            url_for("teacher_assignment.teacher_assignments")
        )

    return render_template(
        "admin/edit_teacher_assignment.html",
        assignment=assignment,
        teachers=teachers,
        departments=departments,
        subjects=subjects,
        admission_years=admission_years
    )


@teacher_assignment_bp.route(
    "/teacher-assignments/delete/<int:id>"
)
def delete_teacher_assignment(id):

    assignment = TeacherAssignmentModel.get_assignment_by_id(id)

    if not assignment:

        flash(
            "Assignment not found.",
            "danger"
        )

    else:

        TeacherAssignmentModel.delete_assignment(id)

        flash(
            "Teacher assignment deleted successfully.",
            "success"
        )

    return redirect(
        url_for("teacher_assignment.teacher_assignments")
    )