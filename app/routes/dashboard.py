
from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for,
    flash
)

from services.scheduler import attendance_scheduler
from models.attendance_settings_model import AttendanceSettingsModel


dashboard_bp = Blueprint(
    "dashboard",
    __name__
)


# =====================================================
# ADMIN DASHBOARD
# =====================================================

@dashboard_bp.route("/admin/dashboard")
def admin_dashboard():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    scheduler_status = attendance_scheduler.get_status()

    settings = AttendanceSettingsModel.get_settings()

    attendance_enabled = False

    if settings:
        value = settings.get("is_enabled", 0)

        attendance_enabled = str(value).strip().lower() in (
            "1",
            "true",
            "yes",
            "on"
        )

    return render_template(
        "admin/dashboard.html",
        user=session,
        total_students=0,
        total_teachers=0,
        total_departments=0,
        total_attendance=0,
        scheduler_status=scheduler_status,
        attendance_enabled=attendance_enabled
    )


# =====================================================
# GLOBAL ATTENDANCE START
# =====================================================

@dashboard_bp.route(
    "/admin/attendance/start",
    methods=["POST"]
)
def start_global_attendance():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    settings = AttendanceSettingsModel.get_settings()

    if not settings:
        flash(
            "Attendance settings could not be loaded.",
            "danger"
        )

        return redirect(
            url_for("dashboard.admin_dashboard")
        )

    value = settings.get("is_enabled", 0)

    attendance_enabled = str(value).strip().lower() in (
        "1",
        "true",
        "yes",
        "on"
    )

    if not attendance_enabled:

        flash(
            "Please enable Global Attendance in Attendance Settings first.",
            "warning"
        )

        return redirect(
            url_for("dashboard.admin_dashboard")
        )

    started = attendance_scheduler.start()

    if started:

        flash(
            "Global Attendance Scheduler started successfully.",
            "success"
        )

    else:

        flash(
            "Scheduler is already running or a previous worker is still active.",
            "warning"
        )

    return redirect(
        url_for("dashboard.admin_dashboard")
    )


# =====================================================
# GLOBAL ATTENDANCE STOP
# =====================================================

@dashboard_bp.route(
    "/admin/attendance/stop",
    methods=["POST"]
)
def stop_global_attendance():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    stopped = attendance_scheduler.stop()

    if stopped:

        flash(
            "Global Attendance Scheduler stop requested.",
            "warning"
        )

    else:

        flash(
            "Global Attendance Scheduler is already stopped.",
            "info"
        )

    return redirect(
        url_for("dashboard.admin_dashboard")
    )
