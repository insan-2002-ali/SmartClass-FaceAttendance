from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify
)

from models.subject_model import SubjectModel

subject_bp = Blueprint(
    "subject",
    __name__
)


@subject_bp.route("/subjects")
def subjects():

    keyword = request.args.get(
        "keyword",
        ""
    ).strip()

    if keyword:

        subjects = SubjectModel.search_subjects(keyword)

    else:

        subjects = SubjectModel.get_all_subjects()

    return render_template(
        "admin/subjects.html",
        subjects=subjects,
        keyword=keyword
    )


@subject_bp.route(
    "/subjects/add",
    methods=["GET", "POST"]
)
def add_subject():

    if request.method == "POST":

        subject_code = request.form["subject_code"].strip()
        subject_name = request.form["subject_name"].strip()
        credit = request.form["credit"].strip()
        description = request.form["description"].strip()
        status = request.form["status"]

        if SubjectModel.subject_code_exists(subject_code):

            flash(
                "Subject Code already exists.",
                "danger"
            )

            return render_template(
                "admin/add_subject.html"
            )

        SubjectModel.add_subject({

            "subject_code": subject_code,
            "subject_name": subject_name,
            "credit": credit,
            "description": description,
            "status": status

        })

        flash(
            "Subject added successfully.",
            "success"
        )

        return redirect(
            url_for("subject.subjects")
        )

    return render_template(
        "admin/add_subject.html"
    )


@subject_bp.route(
    "/subjects/edit/<int:id>",
    methods=["GET", "POST"]
)
def edit_subject(id):

    subject = SubjectModel.get_subject_by_id(id)

    if not subject:

        flash(
            "Subject not found.",
            "danger"
        )

        return redirect(
            url_for("subject.subjects")
        )

    if request.method == "POST":

        subject_code = request.form["subject_code"].strip()
        subject_name = request.form["subject_name"].strip()
        credit = request.form["credit"].strip()
        description = request.form["description"].strip()
        status = request.form["status"]

        if SubjectModel.subject_code_exists_for_update(
            subject_code,
            id
        ):

            flash(
                "Subject Code already exists.",
                "danger"
            )

            return render_template(
                "admin/edit_subject.html",
                subject=subject
            )

        SubjectModel.update_subject({

            "id": id,
            "subject_code": subject_code,
            "subject_name": subject_name,
            "credit": credit,
            "description": description,
            "status": status

        })

        flash(
            "Subject updated successfully.",
            "success"
        )

        return redirect(
            url_for("subject.subjects")
        )

    return render_template(
        "admin/edit_subject.html",
        subject=subject
    )


@subject_bp.route("/subjects/delete/<int:id>")
def delete_subject(id):

    subject = SubjectModel.get_subject_by_id(id)

    if not subject:

        flash(
            "Subject not found.",
            "danger"
        )

        return redirect(
            url_for("subject.subjects")
        )

    SubjectModel.delete_subject(id)

    flash(
        "Subject deleted successfully.",
        "success"
    )

    return redirect(
        url_for("subject.subjects")
    )


@subject_bp.route("/subjects/by-department/<int:department_id>")
def get_subjects_by_department(department_id):

    subjects = SubjectModel.get_subjects_by_department(
        department_id
    )

    return jsonify(subjects)