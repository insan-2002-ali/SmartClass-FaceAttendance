from config import get_db_connection


def get_all_admission_years():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM admission_years
        ORDER BY year DESC
    """)

    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return data


def get_admission_year_by_id(admission_year_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM admission_years
        WHERE id=%s
    """, (admission_year_id,))

    data = cursor.fetchone()

    cursor.close()
    conn.close()

    return data


def add_admission_year(year, status):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM admission_years
        WHERE year=%s
    """, (year,))

    exists = cursor.fetchone()

    if exists:

        cursor.close()
        conn.close()

        return False, "Admission Year already exists."

    cursor.execute("""
        INSERT INTO admission_years
        (
            year,
            status
        )
        VALUES
        (
            %s,
            %s
        )
    """, (year, status))

    conn.commit()

    cursor.close()
    conn.close()

    return True, "Admission Year added successfully."


def update_admission_year(admission_year_id, year, status):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE admission_years
        SET
            year=%s,
            status=%s
        WHERE id=%s
    """, (year, status, admission_year_id))

    conn.commit()

    cursor.close()
    conn.close()

    return True, "Admission Year updated successfully."


def delete_admission_year(admission_year_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM admission_years
        WHERE id=%s
    """, (admission_year_id,))

    conn.commit()

    cursor.close()
    conn.close()

    return True