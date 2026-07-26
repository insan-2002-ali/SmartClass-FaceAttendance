from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from config import get_db_connection

auth = Blueprint("auth", __name__)


@auth.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        user_id = request.form.get("user_id")
        password = request.form.get("password")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        sql = """
        SELECT *
        FROM users
        WHERE user_id = %s
        AND password = %s
        """

        cursor.execute(sql, (user_id, password))

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:

            session["user_id"] = user["user_id"]
            session["full_name"] = user["full_name"]
            session["role"] = user["role"]

            return redirect(url_for("dashboard.home"))

        flash("Invalid User ID or Password", "danger")

    return render_template("auth/login.html")


@auth.route("/logout")
def logout():

    session.clear()

    flash("You have logged out successfully.", "success")

    return redirect(url_for("auth.login"))