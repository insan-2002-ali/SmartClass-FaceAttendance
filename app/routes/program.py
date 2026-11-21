from flask import Blueprint, render_template, request, redirect, url_for, session

from models.program_model import (
    get_all_programs,
    get_all_admission_years,
    get_program_by_id,
    add_program,
    update_program,
    delete_program
)

program_bp = Blueprint("program", __name__)


@program_bp.route("/programs")
def programs():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    search = request.args.get("search", "").strip()
    admission_year = request.args.get("admission_year", "")
    degree = request.args.get("degree", "")
    status = request.args.get("status", "")

    programs = get_all_programs(
        search,
        admission_year,
        degree,
        status
    )

    years = get_all_admission_years()

    return render_template(
        "admin/programs.html",
        programs=programs,
        years=years,
        search=search,
        admission_year=admission_year,
        degree=degree,
        status=status
    )


@program_bp.route("/add-program", methods=["GET", "POST"])
def add_program_page():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    years = get_all_admission_years()

    if request.method == "POST":

        success, message = add_program(
            request.form["admission_year_id"],
            request.form["program_code"].upper(),
            request.form["program_name"],
            request.form["degree"],
            request.form["status"]
        )

        if success:
            return redirect(url_for("program.programs"))

        return render_template(
            "admin/add_program.html",
            years=years,
            error=message
        )

    return render_template(
        "admin/add_program.html",
        years=years
    )


@program_bp.route("/edit-program/<int:program_id>", methods=["GET", "POST"])
def edit_program_page(program_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    program = get_program_by_id(program_id)
    years = get_all_admission_years()

    if not program:
        return redirect(url_for("program.programs"))

    if request.method == "POST":

        update_program(
            program_id,
            request.form["admission_year_id"],
            request.form["program_code"].upper(),
            request.form["program_name"],
            request.form["degree"],
            request.form["status"]
        )

        return redirect(url_for("program.programs"))

    return render_template(
        "admin/edit_program.html",
        program=program,
        years=years
    )


@program_bp.route("/delete-program/<int:program_id>")
def delete_program_page(program_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    delete_program(program_id)

    return redirect(url_for("program.programs"))