from database.db import get_db_connection


class SubjectModel:

    @staticmethod
    def get_all_subjects():

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT
            id,
            subject_code,
            subject_name,
            credit,
            description,
            status
        FROM subjects
        ORDER BY id DESC
        """

        cursor.execute(query)

        subjects = cursor.fetchall()

        cursor.close()
        connection.close()

        return subjects


    @staticmethod
    def get_subject_by_id(id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM subjects
            WHERE id=%s
            """,
            (id,)
        )

        subject = cursor.fetchone()

        cursor.close()
        connection.close()

        return subject

    @staticmethod
    def add_subject(data):

        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
        INSERT INTO subjects
        (
            subject_code,
            subject_name,
            credit,
            description,
            status
        )
        VALUES
        (%s,%s,%s,%s,%s)
        """

        values = (
            data["subject_code"],
            data["subject_name"],
            data["credit"],
            data["description"],
            data["status"]
        )

        cursor.execute(query, values)

        connection.commit()

        cursor.close()
        connection.close()


    @staticmethod
    def update_subject(data):

        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
        UPDATE subjects
        SET
            subject_code=%s,
            subject_name=%s,
            credit=%s,
            description=%s,
            status=%s
        WHERE id=%s
        """

        values = (
            data["subject_code"],
            data["subject_name"],
            data["credit"],
            data["description"],
            data["status"],
            data["id"]
        )

        cursor.execute(query, values)

        connection.commit()

        cursor.close()
        connection.close()


    @staticmethod
    def delete_subject(id):

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM subjects WHERE id=%s",
            (id,)
        )

        connection.commit()

        cursor.close()
        connection.close()

    @staticmethod
    def subject_code_exists(subject_code):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id
            FROM subjects
            WHERE subject_code=%s
            """,
            (subject_code,)
        )

        subject = cursor.fetchone()

        cursor.close()
        connection.close()

        return subject


    @staticmethod
    def subject_code_exists_for_update(subject_code, id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id
            FROM subjects
            WHERE subject_code=%s
            AND id<>%s
            """,
            (subject_code, id)
        )

        subject = cursor.fetchone()

        cursor.close()
        connection.close()

        return subject


    @staticmethod
    def search_subjects(keyword):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT
            id,
            subject_code,
            subject_name,
            credit,
            description,
            status
        FROM subjects
        WHERE
            subject_code LIKE %s
            OR subject_name LIKE %s
        ORDER BY id DESC
        """

        search = f"%{keyword}%"

        cursor.execute(
            query,
            (search, search)
        )

        subjects = cursor.fetchall()

        cursor.close()
        connection.close()

        return subjects