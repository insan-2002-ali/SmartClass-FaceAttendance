from database.db import get_db_connection
from mysql.connector import Error
import bcrypt


class StudentModel:

    @staticmethod
    def get_all_students():

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT
            s.id,
            s.student_id,
            s.full_name,
            s.email,
            s.phone,
            s.gender,
            s.date_of_birth,
            s.profile_photo,
            s.status,
            p.program_name,
            d.department_name,
            ay.year AS admission_year
        FROM students s
        LEFT JOIN programs p
            ON s.program_id = p.id
        LEFT JOIN departments d
            ON s.department_id = d.id
        LEFT JOIN admission_years ay
            ON p.admission_year_id = ay.id
        ORDER BY s.id DESC
        """

        cursor.execute(query)

        students = cursor.fetchall()

        cursor.close()
        connection.close()

        return students


    @staticmethod
    def get_student_by_id(id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM students
            WHERE id=%s
            """,
            (id,)
        )

        student = cursor.fetchone()

        cursor.close()
        connection.close()

        return student


    @staticmethod
    def get_programs():

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                program_name
            FROM programs
            WHERE status='Active'
            ORDER BY program_name
        """)

        programs = cursor.fetchall()

        cursor.close()
        connection.close()

        return programs


    @staticmethod
    def get_departments():

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                department_name
            FROM departments
            WHERE status='Active'
            ORDER BY department_name
        """)

        departments = cursor.fetchall()

        cursor.close()
        connection.close()

        return departments


    @staticmethod
    def student_id_exists(student_id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id
            FROM students
            WHERE student_id=%s
            """,
            (student_id,)
        )

        student = cursor.fetchone()

        cursor.close()
        connection.close()

        return student


    @staticmethod
    def email_exists(email):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id
            FROM students
            WHERE email=%s
            """,
            (email,)
        )

        student = cursor.fetchone()

        cursor.close()
        connection.close()

        return student

    @staticmethod
    def add_student(data):

        connection = get_db_connection()
        cursor = connection.cursor()

        hashed_password = bcrypt.hashpw(
            data["password"].encode(),
            bcrypt.gensalt()
        ).decode()

        query = """
        INSERT INTO students
        (
            student_id,
            full_name,
            email,
            phone,
            gender,
            date_of_birth,
            program_id,
            department_id,
            profile_photo,
            password,
            status
        )
        VALUES
        (
            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
        )
        """

        values = (
            data["student_id"],
            data["full_name"],
            data["email"],
            data["phone"],
            data["gender"],
            data["date_of_birth"],
            data["program_id"],
            data["department_id"],
            data["profile_photo"],
            hashed_password,
            data["status"]
        )

        try:

            cursor.execute(query, values)

            connection.commit()

            return True

        except Error:

            connection.rollback()

            return False

        finally:

            cursor.close()
            connection.close()


    @staticmethod
    def update_student(data):

        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
        UPDATE students
        SET
            student_id=%s,
            full_name=%s,
            email=%s,
            phone=%s,
            gender=%s,
            date_of_birth=%s,
            program_id=%s,
            department_id=%s,
            profile_photo=%s,
            status=%s
        WHERE id=%s
        """

        values = (
            data["student_id"],
            data["full_name"],
            data["email"],
            data["phone"],
            data["gender"],
            data["date_of_birth"],
            data["program_id"],
            data["department_id"],
            data["profile_photo"],
            data["status"],
            data["id"]
        )

        try:

            cursor.execute(query, values)

            connection.commit()

            return True

        except Error:

            connection.rollback()

            return False

        finally:

            cursor.close()
            connection.close()


    @staticmethod
    def delete_student(id):

        connection = get_db_connection()
        cursor = connection.cursor()

        try:

            cursor.execute(
                """
                DELETE FROM students
                WHERE id=%s
                """,
                (id,)
            )

            connection.commit()

            return True

        except Error:

            connection.rollback()

            return False

        finally:

            cursor.close()
            connection.close()


    @staticmethod
    def student_id_exists_for_update(student_id, id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id
            FROM students
            WHERE student_id=%s
            AND id<>%s
            """,
            (student_id, id)
        )

        student = cursor.fetchone()

        cursor.close()
        connection.close()

        return student


    @staticmethod
    def email_exists_for_update(email, id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id
            FROM students
            WHERE email=%s
            AND id<>%s
            """,
            (email, id)
        )

        student = cursor.fetchone()

        cursor.close()
        connection.close()

        return student


    @staticmethod
    def count_students():

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM students
            """
        )

        total = cursor.fetchone()[0]

        cursor.close()
        connection.close()

        return total


    @staticmethod
    def search_students(keyword=""):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT
            s.id,
            s.student_id,
            s.full_name,
            s.email,
            s.phone,
            s.gender,
            s.date_of_birth,
            s.profile_photo,
            s.status,
            p.program_name,
            d.department_name,
            ay.year AS admission_year
        FROM students s
        LEFT JOIN programs p
            ON s.program_id = p.id
        LEFT JOIN departments d
            ON s.department_id = d.id
        LEFT JOIN admission_years ay
            ON p.admission_year_id = ay.id
        WHERE
            s.student_id LIKE %s
            OR s.full_name LIKE %s
            OR s.email LIKE %s
            OR s.phone LIKE %s
            OR p.program_name LIKE %s
            OR d.department_name LIKE %s
            OR ay.year LIKE %s
        ORDER BY s.id DESC
        """

        value = "%" + keyword + "%"

        cursor.execute(
            query,
            (
                value,
                value,
                value,
                value,
                value,
                value,
                value
            )
        )

        students = cursor.fetchall()

        cursor.close()
        connection.close()

        return students