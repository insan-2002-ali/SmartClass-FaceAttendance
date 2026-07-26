from flask import Blueprint, render_template, session, redirect, url_for

dashboard = Blueprint("dashboard", __name__)


@dashboard.route("/dashboard")
def home():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    return render_template("admin/dashboard.html")