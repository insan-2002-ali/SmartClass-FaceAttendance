from flask import Blueprint, render_template, request, redirect, url_for, session
from config import get_db_connection

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def home():
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["user_id"].strip()
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE username=%s
            AND password=%s
            AND status='Active'
            """,
            (
                username,
                password
            )
        )

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["full_name"] = user["full_name"]
            session["role"] = user["role"]

            if user["role"] == "Admin":
                return redirect(url_for("dashboard.admin_dashboard"))

            elif user["role"] == "Teacher":
                return "Teacher Dashboard"

            elif user["role"] == "Student":
                return "Student Dashboard"

        return render_template(
            "auth/login.html",
            error="Invalid Username or Password"
        )

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("auth.login"))