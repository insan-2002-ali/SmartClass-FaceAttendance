from database.db import get_db_connection
from mysql.connector import Error


class StudentEnrollmentModel:

    @staticmethod
    def get_all_students():

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT
            id,
            student_id,
            full_name
        FROM students
        WHERE status='Active'
        ORDER BY full_name
        """

        cursor.execute(query)

        students = cursor.fetchall()

        cursor.close()
        connection.close()

        return students

    @staticmethod
    def get_all_teacher_assignments():

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT
            ta.id,

            t.full_name AS teacher_name,

            s.subject_name,

            d.department_name,

            ay.year,

            ta.semester,

            ta.section

        FROM teacher_assignments ta

        LEFT JOIN teachers t
            ON ta.teacher_id = t.id

        LEFT JOIN subjects s
            ON ta.subject_id = s.id

        LEFT JOIN departments d
            ON ta.department_id = d.id

        LEFT JOIN admission_years ay
            ON ta.admission_year_id = ay.id

        WHERE ta.status='Active'

        ORDER BY
            d.department_name,
            ta.semester,
            ta.section
        """

        cursor.execute(query)

        assignments = cursor.fetchall()

        cursor.close()
        connection.close()

        return assignments

    @staticmethod
    def get_all_enrollments():

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT

            se.id,

            st.student_id,

            st.full_name,

            t.full_name AS teacher_name,

            sub.subject_name,

            d.department_name,

            ay.year,

            ta.semester,

            ta.section,

            se.status

        FROM student_enrollments se

        INNER JOIN students st
            ON se.student_id = st.id

        INNER JOIN teacher_assignments ta
            ON se.teacher_assignment_id = ta.id

        INNER JOIN teachers t
            ON ta.teacher_id = t.id

        INNER JOIN subjects sub
            ON ta.subject_id = sub.id

        INNER JOIN departments d
            ON ta.department_id = d.id

        INNER JOIN admission_years ay
            ON ta.admission_year_id = ay.id

        ORDER BY
            st.full_name ASC
        """

        cursor.execute(query)

        enrollments = cursor.fetchall()

        cursor.close()
        connection.close()

        return enrollments

    @staticmethod
    def add_enrollment(data):

        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
        INSERT INTO student_enrollments
        (
            student_id,
            teacher_assignment_id,
            status
        )
        VALUES
        (
            %s,
            %s,
            %s
        )
        """

        values = (
            data["student_id"],
            data["teacher_assignment_id"],
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
    def get_enrollment_by_id(id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT *
        FROM student_enrollments
        WHERE id=%s
        """

        cursor.execute(
            query,
            (id,)
        )

        enrollment = cursor.fetchone()

        cursor.close()
        connection.close()

        return enrollment


    @staticmethod
    def update_enrollment(data):

        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
        UPDATE student_enrollments
        SET
            student_id=%s,
            teacher_assignment_id=%s,
            status=%s
        WHERE id=%s
        """

        values = (
            data["student_id"],
            data["teacher_assignment_id"],
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
    def delete_enrollment(id):

        connection = get_db_connection()
        cursor = connection.cursor()

        try:

            cursor.execute(
                """
                DELETE
                FROM student_enrollments
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
    def enrollment_exists(student_id, teacher_assignment_id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT id
        FROM student_enrollments
        WHERE
            student_id=%s
            AND teacher_assignment_id=%s
        """

        cursor.execute(
            query,
            (
                student_id,
                teacher_assignment_id
            )
        )

        enrollment = cursor.fetchone()

        cursor.close()
        connection.close()

        return enrollment

    @staticmethod
    def enrollment_exists_for_update(
        student_id,
        teacher_assignment_id,
        id
    ):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT id
        FROM student_enrollments
        WHERE
            student_id=%s
            AND teacher_assignment_id=%s
            AND id<>%s
        """

        cursor.execute(
            query,
            (
                student_id,
                teacher_assignment_id,
                id
            )
        )

        enrollment = cursor.fetchone()

        cursor.close()
        connection.close()

        return enrollment
    @staticmethod
    def search_enrollments(keyword=""):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT

            se.id,

            st.student_id,

            st.full_name,

            t.full_name AS teacher_name,

            sub.subject_name,

            d.department_name,

            ay.year,

            ta.semester,

            ta.section,

            se.status

        FROM student_enrollments se

        INNER JOIN students st
            ON se.student_id = st.id

        INNER JOIN teacher_assignments ta
            ON se.teacher_assignment_id = ta.id

        INNER JOIN teachers t
            ON ta.teacher_id = t.id

        INNER JOIN subjects sub
            ON ta.subject_id = sub.id

        INNER JOIN departments d
            ON ta.department_id = d.id

        INNER JOIN admission_years ay
            ON ta.admission_year_id = ay.id

        WHERE

            st.student_id LIKE %s

            OR st.full_name LIKE %s

            OR t.full_name LIKE %s

            OR sub.subject_name LIKE %s

            OR d.department_name LIKE %s

        ORDER BY st.full_name
        """

        value = "%" + keyword + "%"

        cursor.execute(
            query,
            (
                value,
                value,
                value,
                value,
                value
            )
        )

        enrollments = cursor.fetchall()

        cursor.close()
        connection.close()

        return enrollments