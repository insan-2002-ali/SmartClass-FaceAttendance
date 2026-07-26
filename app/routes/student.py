from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from config import get_db_connection

student = Blueprint("student", __name__)


@student.route("/students")
def students():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM students ORDER BY id DESC")

    students = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin/students.html",
        students=students
    )


@student.route("/students/add", methods=["GET", "POST"])
def add_student():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "POST":

        student_id = request.form["student_id"]
        full_name = request.form["full_name"]
        department = request.form["department"]
        semester = request.form["semester"]
        email = request.form["email"]
        phone = request.form["phone"]

        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
        INSERT INTO students
        (student_id, full_name, department, semester, email, phone)
        VALUES (%s,%s,%s,%s,%s,%s)
        """

        cursor.execute(sql, (
            student_id,
            full_name,
            department,
            semester,
            email,
            phone
        ))

        conn.commit()

        cursor.close()
        conn.close()

        flash("Student Added Successfully", "success")

        return redirect(url_for("student.students"))

    return render_template("admin/add_student.html")