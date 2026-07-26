from config import get_db_connection
import mysql.connector


def add_department(department_code, department_name, description):

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
        INSERT INTO departments
        (department_code, department_name, description)
        VALUES (%s, %s, %s)
        """

        cursor.execute(
            sql,
            (
                department_code,
                department_name,
                description
            )
        )

        conn.commit()

        return True, "Department added successfully."

    except mysql.connector.IntegrityError:

        if conn:
            conn.rollback()

        return False, "Department Code already exists."

    except mysql.connector.Error as err:

        if conn:
            conn.rollback()

        return False, str(err)

    finally:

        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()


def get_departments():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM departments
        ORDER BY id DESC
    """)

    departments = cursor.fetchall()

    cursor.close()
    conn.close()

    return departments


def get_department_by_id(department_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM departments
        WHERE id=%s
        """,
        (department_id,)
    )

    department = cursor.fetchone()

    cursor.close()
    conn.close()

    return department


def update_department(
        department_id,
        department_code,
        department_name,
        description
):

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE departments
            SET
                department_code=%s,
                department_name=%s,
                description=%s
            WHERE id=%s
            """,
            (
                department_code,
                department_name,
                description,
                department_id
            )
        )

        conn.commit()

        return True, "Department updated successfully."

    except mysql.connector.IntegrityError:

        if conn:
            conn.rollback()

        return False, "Department Code already exists."

    except mysql.connector.Error as err:

        if conn:
            conn.rollback()

        return False, str(err)

    finally:

        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()


def delete_department(department_id):

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM departments
            WHERE id=%s
            """,
            (department_id,)
        )

        conn.commit()

        return True

    except mysql.connector.Error:

        if conn:
            conn.rollback()

        return False

    finally:

        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()