from config import get_db_connection
import mysql.connector


def get_all_admission_years():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id,
            year
        FROM admission_years
        WHERE status = 'Active'
        ORDER BY year DESC
    """)

    years = cursor.fetchall()

    cursor.close()
    conn.close()

    return years


def get_all_programs(
    search="",
    admission_year="",
    degree="",
    status=""
):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    sql = """
        SELECT
            p.*,
            ay.year AS admission_year
        FROM programs p
        INNER JOIN admission_years ay
            ON ay.id = p.admission_year_id
        WHERE 1=1
    """

    values = []

    if search:

        sql += """
            AND (
                p.program_code LIKE %s
                OR p.program_name LIKE %s
            )
        """

        keyword = f"%{search}%"

        values.extend([keyword, keyword])

    if admission_year:

        sql += " AND p.admission_year_id=%s"

        values.append(admission_year)

    if degree:

        sql += " AND p.degree=%s"

        values.append(degree)

    if status:

        sql += " AND p.status=%s"

        values.append(status)

    sql += """
        ORDER BY
            ay.year DESC,
            p.program_name ASC
    """

    cursor.execute(sql, values)

    programs = cursor.fetchall()

    cursor.close()
    conn.close()

    return programs


def get_all_programs_for_dropdown():

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
def add_program(
    admission_year_id,
    program_code,
    program_name,
    degree,
    status
):

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        check_sql = """
            SELECT id
            FROM programs
            WHERE admission_year_id=%s
            AND program_code=%s
            AND degree=%s
        """

        cursor.execute(
            check_sql,
            (
                admission_year_id,
                program_code,
                degree
            )
        )

        if cursor.fetchone():

            return False, "Program Code already exists."

        insert_sql = """
            INSERT INTO programs
            (
                admission_year_id,
                program_code,
                program_name,
                degree,
                status
            )
            VALUES
            (%s,%s,%s,%s,%s)
        """

        cursor.execute(
            insert_sql,
            (
                admission_year_id,
                program_code,
                program_name,
                degree,
                status
            )
        )

        conn.commit()

        return True, "Program added successfully."

    except mysql.connector.Error as err:

        if conn:
            conn.rollback()

        return False, str(err)

    finally:

        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()


def get_program_by_id(program_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM programs
        WHERE id=%s
        """,
        (program_id,)
    )

    program = cursor.fetchone()

    cursor.close()
    conn.close()

    return program
def update_program(
    program_id,
    admission_year_id,
    program_code,
    program_name,
    degree,
    status
):

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        check_sql = """
            SELECT id
            FROM programs
            WHERE admission_year_id=%s
            AND program_code=%s
            AND degree=%s
            AND id<>%s
        """

        cursor.execute(
            check_sql,
            (
                admission_year_id,
                program_code,
                degree,
                program_id
            )
        )

        if cursor.fetchone():

            return False, "Program Code already exists."

        update_sql = """
            UPDATE programs
            SET
                admission_year_id=%s,
                program_code=%s,
                program_name=%s,
                degree=%s,
                status=%s
            WHERE id=%s
        """

        cursor.execute(
            update_sql,
            (
                admission_year_id,
                program_code,
                program_name,
                degree,
                status,
                program_id
            )
        )

        conn.commit()

        return True, "Program updated successfully."

    except mysql.connector.Error as err:

        if conn:
            conn.rollback()

        return False, str(err)

    finally:

        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()


def delete_program(program_id):

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM programs
            WHERE id=%s
            """,
            (program_id,)
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