from config import get_db_connection
import mysql.connector


def get_all_programs():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            p.id,
            p.program_name,
            p.program_code,
            p.degree,
            ay.year AS admission_year
        FROM programs p
        INNER JOIN admission_years ay
            ON ay.id = p.admission_year_id
        WHERE p.status='Active'
        ORDER BY
            ay.year DESC,
            p.program_name ASC
    """)

    programs = cursor.fetchall()

    cursor.close()
    conn.close()

    return programs


def get_all_departments(
    search="",
    program="",
    status=""
):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    sql = """
        SELECT
            d.*,
            p.program_name,
            p.program_code,
            p.degree,
            ay.year AS admission_year
        FROM departments d
        INNER JOIN programs p
            ON d.program_id = p.id
        INNER JOIN admission_years ay
            ON p.admission_year_id = ay.id
        WHERE 1=1
    """

    values = []

    if search:

        sql += """
            AND (
                d.department_code LIKE %s
                OR d.department_name LIKE %s
            )
        """

        keyword = f"%{search}%"

        values.extend([keyword, keyword])

    if program:

        sql += " AND d.program_id=%s"

        values.append(program)

    if status:

        sql += " AND d.status=%s"

        values.append(status)

    sql += """
        ORDER BY
            ay.year DESC,
            p.program_name ASC,
            d.department_name ASC
    """

    cursor.execute(sql, values)

    departments = cursor.fetchall()

    cursor.close()
    conn.close()

    return departments
def add_department(
    program_id,
    department_code,
    department_name,
    description,
    status
):

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        check_sql = """
            SELECT id
            FROM departments
            WHERE program_id=%s
            AND department_code=%s
        """

        cursor.execute(
            check_sql,
            (
                program_id,
                department_code
            )
        )

        if cursor.fetchone():

            return False, "Department Code already exists."

        insert_sql = """
            INSERT INTO departments
            (
                program_id,
                department_code,
                department_name,
                description,
                status
            )
            VALUES
            (%s,%s,%s,%s,%s)
        """

        cursor.execute(
            insert_sql,
            (
                program_id,
                department_code,
                department_name,
                description,
                status
            )
        )

        conn.commit()

        return True, "Department added successfully."

    except mysql.connector.Error as err:

        if conn:
            conn.rollback()

        return False, str(err)

    finally:

        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()


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
    program_id,
    department_code,
    department_name,
    description,
    status
):

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        check_sql = """
            SELECT id
            FROM departments
            WHERE program_id=%s
            AND department_code=%s
            AND id<>%s
        """

        cursor.execute(
            check_sql,
            (
                program_id,
                department_code,
                department_id
            )
        )

        if cursor.fetchone():

            return False, "Department Code already exists."

        update_sql = """
            UPDATE departments
            SET
                program_id=%s,
                department_code=%s,
                department_name=%s,
                description=%s,
                status=%s
            WHERE id=%s
        """

        cursor.execute(
            update_sql,
            (
                program_id,
                department_code,
                department_name,
                description,
                status,
                department_id
            )
        )

        conn.commit()

        return True, "Department updated successfully."

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