from flask import Flask, render_template, request, redirect, url_for, session
from config import get_db_connection
from models.department_model import (
    add_department,
    get_departments,
    get_department_by_id,
    update_department,
    delete_department
)
import os


def create_app():

    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "../templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "../static"),
    )

    app.secret_key = "attendance_system_secret_key"

    print("Root Path :", app.root_path)
    print("Template Path :", app.jinja_loader.searchpath)

    # =========================
    # Home
    # =========================
    @app.route("/")
    def home():
        return redirect(url_for("login"))

    # =========================
    # Login
    # =========================
    @app.route("/login", methods=["GET", "POST"])
    def login():

        if request.method == "POST":

            user_id = request.form["user_id"]
            password = request.form["password"]

            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT *
                FROM users
                WHERE user_id=%s AND password=%s
                """,
                (user_id, password)
            )

            user = cursor.fetchone()

            cursor.close()
            conn.close()

            if user:

                session["user_id"] = user["user_id"]
                session["full_name"] = user["full_name"]
                session["role"] = user["role"]

                if user["role"] == "admin":
                    return redirect(url_for("admin_dashboard"))

                return "Login Successful"

            return render_template(
                "auth/login.html",
                error="Invalid User ID or Password"
            )

        return render_template("auth/login.html")

    # =========================
    # Dashboard
    # =========================
    @app.route("/admin/dashboard")
    def admin_dashboard():

        if "user_id" not in session:
            return redirect(url_for("login"))

        return render_template(
            "admin/dashboard.html",
            user=session
        )

    # =========================
    # Add Department
    # =========================
    @app.route("/add-department", methods=["GET", "POST"])
    def add_department_page():

        if "user_id" not in session:
            return redirect(url_for("login"))

        if request.method == "POST":

            department_code = request.form["department_code"]
            department_name = request.form["department_name"]
            description = request.form["description"]

            success, message = add_department(
                department_code,
                department_name,
                description
            )

            if success:
                return redirect(url_for("departments"))

            return render_template(
                "admin/add_department.html",
                error=message
            )

        return render_template("admin/add_department.html")

    # =========================
    # Department List
    # =========================
    @app.route("/departments")
    def departments():

        if "user_id" not in session:
            return redirect(url_for("login"))

        departments = get_departments()

        return render_template(
            "admin/departments.html",
            departments=departments
        )

    # =========================
    # Edit Department
    # =========================
    @app.route("/edit-department/<int:department_id>", methods=["GET", "POST"])
    def edit_department(department_id):

        if "user_id" not in session:
            return redirect(url_for("login"))

        department = get_department_by_id(department_id)

        if not department:
            return redirect(url_for("departments"))

        if request.method == "POST":

            department_code = request.form["department_code"]
            department_name = request.form["department_name"]
            description = request.form["description"]

            success, message = update_department(
                department_id,
                department_code,
                department_name,
                description
            )

            if success:
                return redirect(url_for("departments"))

            department = get_department_by_id(department_id)

            return render_template(
                "admin/edit_department.html",
                department=department,
                error=message
            )

        return render_template(
            "admin/edit_department.html",
            department=department
        )

    # =========================
    # Delete Department
    # =========================
    @app.route("/delete-department/<int:department_id>")
    def delete_department_route(department_id):

        if "user_id" not in session:
            return redirect(url_for("login"))

        delete_department(department_id)

        return redirect(url_for("departments"))

    # =========================
    # Logout
    # =========================
    @app.route("/logout")
    def logout():

        session.clear()

        return redirect(url_for("login"))

    return app