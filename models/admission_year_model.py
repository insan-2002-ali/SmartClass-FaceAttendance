from config import get_db_connection
import mysql.connector


def add_admission_year(year):

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO admission_years (year)
            VALUES (%s)
            """,
            (year,)
        )

        conn.commit()

        return True, "Admission Year added successfully."

    except mysql.connector.IntegrityError:

        if conn:
            conn.rollback()

        return False, "Admission Year already exists."

    except mysql.connector.Error as err:

        if conn:
            conn.rollback()

        return False, str(err)

    finally:

        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()


def get_admission_years():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM admission_years
        ORDER BY year DESC
        """
    )

    years = cursor.fetchall()

    cursor.close()
    conn.close()

    return years


def get_admission_year_by_id(year_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM admission_years
        WHERE id=%s
        """,
        (year_id,)
    )

    year = cursor.fetchone()

    cursor.close()
    conn.close()

    return year


def update_admission_year(year_id, year, status):

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE admission_years
            SET
                year=%s,
                status=%s
            WHERE id=%s
            """,
            (
                year,
                status,
                year_id
            )
        )

        conn.commit()

        return True, "Admission Year updated successfully."

    except mysql.connector.IntegrityError:

        if conn:
            conn.rollback()

        return False, "Admission Year already exists."

    except mysql.connector.Error as err:

        if conn:
            conn.rollback()

        return False, str(err)

    finally:

        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()


def delete_admission_year(year_id):

    conn = None
    cursor = None

    try:

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM admission_years
            WHERE id=%s
            """,
            (year_id,)
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