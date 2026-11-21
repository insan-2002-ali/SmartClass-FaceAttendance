
from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from models.class_schedule_model import ClassScheduleModel


class_schedule_bp = Blueprint(
    "class_schedule",
    __name__
)


DAYS = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday"
]


def prepare_schedule_data(form):

    try:
        class_id = int(form.get("class_id", ""))

        day_of_week = form.get(
            "day_of_week", ""
        ).strip()

        start_time = form.get(
            "start_time", ""
        ).strip()

        end_time = form.get(
            "end_time", ""
        ).strip()

        if not class_id:
            return None, "Please select a class."

        if day_of_week not in DAYS:
            return None, "Please select a valid day."

        if not start_time or not end_time:
            return None, "Please enter class start and end time."

        start = datetime.strptime(start_time, "%H:%M")
        end = datetime.strptime(end_time, "%H:%M")

        duration = int(
            (end - start).total_seconds() / 60
        )

        if duration <= 0:
            return None, "End time must be after start time."

        status = form.get(
            "status", "Active"
        ).strip()

        if status not in ["Active", "Inactive"]:
            return None, "Invalid routine status."

        data = {
            "class_id": class_id,
            "day_of_week": day_of_week,
            "start_time": start_time,
            "end_time": end_time,
            "room_no": form.get("room_no", "").strip() or None,
            "building": form.get("building", "").strip() or None,
            "status": status
        }

        return data, None

    except ValueError:
        return None, "Please enter valid class information and times."


# ==========================================================
# CLASS SCHEDULE LIST
# ==========================================================

@class_schedule_bp.route("/class-schedules")
def class_schedules():

    try:
        schedules = ClassScheduleModel.get_all_schedules()

        return render_template(
            "admin/class_schedules.html",
            schedules=schedules
        )

    except Exception as error:
        flash(
            f"Could not load class routines: {error}",
            "danger"
        )

        return render_template(
            "admin/class_schedules.html",
            schedules=[]
        )


# ==========================================================
# ADD CLASS ROUTINE
# ==========================================================

@class_schedule_bp.route(
    "/class-schedules/add",
    methods=["GET", "POST"]
)
def add_class_schedule():

    classes = ClassScheduleModel.get_all_classes()

    if request.method == "POST":

        data, error = prepare_schedule_data(request.form)

        if error:
            flash(error, "danger")

            return render_template(
                "admin/add_class_schedule.html",
                classes=classes,
                days=DAYS
            )

        try:
            ClassScheduleModel.add_schedule(data)

            flash(
                "Class routine added successfully.",
                "success"
            )

            return redirect(
                url_for("class_schedule.class_schedules")
            )

        except Exception as error:
            flash(
                f"Could not add class routine: {error}",
                "danger"
            )

    return render_template(
        "admin/add_class_schedule.html",
        classes=classes,
        days=DAYS
    )


# ==========================================================
# EDIT CLASS ROUTINE
# ==========================================================

@class_schedule_bp.route(
    "/class-schedules/edit/<int:id>",
    methods=["GET", "POST"]
)
def edit_class_schedule(id):

    schedule = ClassScheduleModel.get_schedule_by_id(id)

    if not schedule:
        flash("Class routine not found.", "danger")

        return redirect(
            url_for("class_schedule.class_schedules")
        )

    classes = ClassScheduleModel.get_all_classes()

    if request.method == "POST":

        data, error = prepare_schedule_data(request.form)

        if error:
            flash(error, "danger")

            return render_template(
                "admin/add_class_schedule.html",
                classes=classes,
                days=DAYS,
                schedule=schedule
            )

        try:
            ClassScheduleModel.update_schedule(id, data)

            flash(
                "Class routine updated successfully.",
                "success"
            )

            return redirect(
                url_for("class_schedule.class_schedules")
            )

        except Exception as error:
            flash(
                f"Could not update class routine: {error}",
                "danger"
            )

    return render_template(
        "admin/add_class_schedule.html",
        classes=classes,
        days=DAYS,
        schedule=schedule
    )


# ==========================================================
# DELETE CLASS ROUTINE
# ==========================================================

@class_schedule_bp.route(
    "/class-schedules/delete/<int:id>",
    methods=["POST"]
)
def delete_class_schedule(id):

    schedule = ClassScheduleModel.get_schedule_by_id(id)

    if not schedule:
        flash("Class routine not found.", "danger")

        return redirect(
            url_for("class_schedule.class_schedules")
        )

    try:
        ClassScheduleModel.delete_schedule(id)

        flash(
            "Class routine deleted successfully.",
            "success"
        )

    except Exception as error:
        flash(
            f"Could not delete class routine: {error}",
            "danger"
        )

    return redirect(
        url_for("class_schedule.class_schedules")
    )
