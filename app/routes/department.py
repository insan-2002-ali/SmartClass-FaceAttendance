from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from models.department_model import (
    get_all_departments,
    get_department_by_id,
    add_department,
    update_department,
    delete_department
)

from models.program_model import (
    get_all_programs_for_dropdown
)

department_bp = Blueprint("department", __name__)


@department_bp.route("/departments")
def departments():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    search = request.args.get("search", "").strip()
    program_id = request.args.get("program_id", "")
    status = request.args.get("status", "")

    departments = get_all_departments(
        search,
        program_id,
        status
    )

    programs = get_all_programs_for_dropdown()

    return render_template(
        "admin/departments.html",
        departments=departments,
        programs=programs,
        search=search,
        program_id=program_id,
        status=status
    )


@department_bp.route("/departments/add", methods=["GET", "POST"])
def add_department_page():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    programs = get_all_programs_for_dropdown()

    if request.method == "POST":

        program_id = request.form.get("program_id")
        department_code = request.form.get("department_code", "").strip()
        department_name = request.form.get("department_name", "").strip()
        description = request.form.get("description", "").strip()
        status = request.form.get("status")

        success, message = add_department(
            program_id,
            department_code,
            department_name,
            description,
            status
        )

        flash(message, "success" if success else "danger")

        if success:
            return redirect(url_for("department.departments"))

    return render_template(
        "admin/add_department.html",
        programs=programs
    )


@department_bp.route("/departments/edit/<int:department_id>", methods=["GET", "POST"])
def edit_department_page(department_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    department = get_department_by_id(department_id)

    if not department:
        flash("Department not found.", "danger")
        return redirect(url_for("department.departments"))

    programs = get_all_programs_for_dropdown()

    if request.method == "POST":

        program_id = request.form.get("program_id")
        department_code = request.form.get("department_code", "").strip()
        department_name = request.form.get("department_name", "").strip()
        description = request.form.get("description", "").strip()
        status = request.form.get("status")

        success, message = update_department(
            department_id,
            program_id,
            department_code,
            department_name,
            description,
            status
        )

        flash(message, "success" if success else "danger")

        if success:
            return redirect(url_for("department.departments"))

    return render_template(
        "admin/edit_department.html",
        department=department,
        programs=programs
    )


@department_bp.route("/departments/delete/<int:department_id>")
def delete_department_page(department_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    success = delete_department(department_id)

    if success:
        flash("Department deleted successfully.", "success")
    else:
        flash("Failed to delete department.", "danger")

    return redirect(url_for("department.departments"))