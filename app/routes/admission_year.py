from flask import Blueprint, render_template, request, redirect, url_for, session

from models.admission_year_model import (
    get_all_admission_years,
    get_admission_year_by_id,
    add_admission_year,
    update_admission_year,
    delete_admission_year
)

admission_year_bp = Blueprint("admission_year", __name__)


@admission_year_bp.route("/admission-years")
def admission_years():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    years = get_all_admission_years()

    return render_template(
        "admin/admission_years.html",
        years=years
    )


@admission_year_bp.route("/add-admission-year", methods=["GET", "POST"])
def add_admission_year_page():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "POST":

        year = request.form["year"]
        status = request.form["status"]

        success, message = add_admission_year(
            year,
            status
        )

        if success:
            return redirect(url_for("admission_year.admission_years"))

        return render_template(
            "admin/add_admission_year.html",
            error=message
        )

    return render_template("admin/add_admission_year.html")


@admission_year_bp.route("/edit-admission-year/<int:admission_year_id>", methods=["GET", "POST"])
def edit_admission_year_page(admission_year_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    year = get_admission_year_by_id(admission_year_id)

    if not year:
        return redirect(url_for("admission_year.admission_years"))

    if request.method == "POST":

        update_admission_year(
            admission_year_id,
            request.form["year"],
            request.form["status"]
        )

        return redirect(url_for("admission_year.admission_years"))

    return render_template(
        "admin/edit_admission_year.html",
        year=year
    )


@admission_year_bp.route("/delete-admission-year/<int:admission_year_id>")
def delete_admission_year_page(admission_year_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    delete_admission_year(admission_year_id)

    return redirect(url_for("admission_year.admission_years"))