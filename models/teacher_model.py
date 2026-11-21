from database.db import get_db_connection
from mysql.connector import Error
import bcrypt


class TeacherModel:

    @staticmethod
    def get_all_teachers():

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT
            t.id,
            t.teacher_id,
            t.full_name,
            t.email,
            t.phone,
            t.gender,
            t.designation,
            t.profile_photo,
            t.status,
            d.department_name
        FROM teachers t
        LEFT JOIN departments d
            ON t.department_id = d.id
        ORDER BY t.id DESC
        """

        cursor.execute(query)

        teachers = cursor.fetchall()

        cursor.close()
        connection.close()

        return teachers


    @staticmethod
    def get_teacher_by_id(id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM teachers
            WHERE id=%s
            """,
            (id,)
        )

        teacher = cursor.fetchone()

        cursor.close()
        connection.close()

        return teacher


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
    def teacher_id_exists(teacher_id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id
            FROM teachers
            WHERE teacher_id=%s
            """,
            (teacher_id,)
        )

        teacher = cursor.fetchone()

        cursor.close()
        connection.close()

        return teacher


    @staticmethod
    def email_exists(email):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id
            FROM teachers
            WHERE email=%s
            """,
            (email,)
        )

        teacher = cursor.fetchone()

        cursor.close()
        connection.close()

        return teacher


    @staticmethod
    def add_teacher(data):

        connection = get_db_connection()
        cursor = connection.cursor()

        hashed_password = bcrypt.hashpw(
            data["password"].encode(),
            bcrypt.gensalt()
        ).decode()

        query = """
        INSERT INTO teachers
        (
            teacher_id,
            full_name,
            email,
            phone,
            gender,
            designation,
            department_id,
            profile_photo,
            password,
            status
        )
        VALUES
        (
            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s
        )
        """

        values = (
            data["teacher_id"],
            data["full_name"],
            data["email"],
            data["phone"],
            data["gender"],
            data["designation"],
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
    def update_teacher(data):

        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
        UPDATE teachers
        SET
            teacher_id=%s,
            full_name=%s,
            email=%s,
            phone=%s,
            gender=%s,
            designation=%s,
            department_id=%s,
            profile_photo=%s,
            status=%s
        WHERE id=%s
        """

        values = (
            data["teacher_id"],
            data["full_name"],
            data["email"],
            data["phone"],
            data["gender"],
            data["designation"],
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
    def delete_teacher(id):

        connection = get_db_connection()
        cursor = connection.cursor()

        try:

            cursor.execute(
                """
                DELETE FROM teachers
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
    def teacher_id_exists_for_update(
        teacher_id,
        id
    ):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id
            FROM teachers
            WHERE teacher_id=%s
            AND id<>%s
            """,
            (
                teacher_id,
                id
            )
        )

        teacher = cursor.fetchone()

        cursor.close()
        connection.close()

        return teacher


    @staticmethod
    def email_exists_for_update(
        email,
        id
    ):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id
            FROM teachers
            WHERE email=%s
            AND id<>%s
            """,
            (
                email,
                id
            )
        )

        teacher = cursor.fetchone()

        cursor.close()
        connection.close()

        return teacher


    @staticmethod
    def search_teachers(keyword="", department_id=""):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT
            t.id,
            t.teacher_id,
            t.full_name,
            t.email,
            t.phone,
            t.gender,
            t.designation,
            t.profile_photo,
            t.status,
            d.department_name
        FROM teachers t
        LEFT JOIN departments d
            ON t.department_id = d.id
        WHERE 1=1
        """

        values = []

        if keyword:

            query += """
            AND
            (
                t.teacher_id LIKE %s
                OR t.full_name LIKE %s
                OR t.email LIKE %s
                OR t.phone LIKE %s
                OR t.designation LIKE %s
            )
            """

            search = f"%{keyword}%"

            values.extend([
                search,
                search,
                search,
                search,
                search
            ])

        if department_id:

            query += " AND t.department_id=%s"

            values.append(department_id)

        query += " ORDER BY t.id DESC"

        cursor.execute(
            query,
            tuple(values)
        )

        teachers = cursor.fetchall()

        cursor.close()
        connection.close()

        return teachers


    @staticmethod
    def count_teachers():

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM teachers
            """
        )

        total = cursor.fetchone()[0]

        cursor.close()
        connection.close()

        return total


    @staticmethod
    def get_department_teacher_count():

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT
            d.id,
            d.department_name,
            COUNT(t.id) AS total_teachers
        FROM departments d
        LEFT JOIN teachers t
            ON d.id = t.department_id
        GROUP BY
            d.id,
            d.department_name
        ORDER BY
            d.department_name
        """

        cursor.execute(query)

        departments = cursor.fetchall()

        cursor.close()
        connection.close()

        return departments           