
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from models.attendance_settings_model import AttendanceSettingsModel


attendance_settings_bp = Blueprint(
    "attendance_settings",
    __name__
)


TIMING_FIELDS = [
    "preparation_minutes",
    "check1_start_min",
    "check1_end_min",
    "check1_camera_minutes",
    "check2_start_min",
    "check2_end_min",
    "check2_camera_minutes",
    "break_start_min",
    "break_end_min",
    "check3_start_min",
    "check3_end_min",
    "check3_camera_minutes",
    "minimum_present_checks"
]


def prepare_settings_data(form):

    try:
        data = {}

        for field in TIMING_FIELDS:
            value = form.get(field, "").strip()

            if not value:
                return None, f"{field} is required."

            data[field] = int(value)

            if data[field] < 0:
                return None, f"{field} cannot be negative."

        if data["preparation_minutes"] < 0:
            return None, "Preparation time cannot be negative."

        if data["minimum_present_checks"] not in [1, 2, 3]:
            return None, "Minimum present checks must be 1, 2, or 3."

        if not (
            0 <= data["check1_start_min"]
            < data["check1_end_min"]
            <= data["check2_start_min"]
            < data["check2_end_min"]
            <= data["break_start_min"]
            < data["break_end_min"]
            <= data["check3_start_min"]
            < data["check3_end_min"]
        ):
            return None, (
                "Invalid timing order. Required order: "
                "Check 1 → Check 2 → Break → Check 3."
            )

        for number in [1, 2, 3]:

            window_start = data[f"check{number}_start_min"]
            window_end = data[f"check{number}_end_min"]
            camera_minutes = data[f"check{number}_camera_minutes"]

            if camera_minutes <= 0:
                return None, (
                    f"Check {number} camera duration must be greater than zero."
                )

            if camera_minutes > window_end - window_start:
                return None, (
                    f"Check {number} camera duration cannot exceed its window."
                )

        return data, None

    except ValueError:
        return None, "Please enter valid whole numbers."


# ==========================================================
# GLOBAL ATTENDANCE SETTINGS
# ==========================================================

@attendance_settings_bp.route(
    "/attendance-settings",
    methods=["GET", "POST"]
)
def attendance_settings():

    if request.method == "POST":

        data, error = prepare_settings_data(request.form)

        if error:
            flash(error, "danger")

        else:
            try:
                AttendanceSettingsModel.update_settings(data)

                flash(
                    "Global attendance settings updated successfully.",
                    "success"
                )

                return redirect(
                    url_for("attendance_settings.attendance_settings")
                )

            except Exception as error:
                flash(
                    f"Could not update attendance settings: {error}",
                    "danger"
                )

    try:
        settings = AttendanceSettingsModel.get_settings()

        if not settings:
            flash(
                "Global attendance settings record was not found.",
                "danger"
            )

        return render_template(
            "admin/attendance_settings.html",
            settings=settings
        )

    except Exception as error:
        flash(
            f"Could not load attendance settings: {error}",
            "danger"
        )

        return redirect(
            url_for("dashboard.dashboard")
        )
