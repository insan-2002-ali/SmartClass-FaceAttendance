from database.db import get_db_connection


class TeacherAssignmentModel:

    @staticmethod
    def get_all_assignments():

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT
            ta.id,
            t.full_name AS teacher_name,
            d.department_name,
            s.subject_name,
            ay.year,
            ta.semester,
            ta.section,
            ta.academic_year,
            ta.status
        FROM teacher_assignments ta
        INNER JOIN teachers t
            ON ta.teacher_id=t.id
        INNER JOIN departments d
            ON ta.department_id=d.id
        INNER JOIN subjects s
            ON ta.subject_id=s.id
        INNER JOIN admission_years ay
            ON ta.admission_year_id=ay.id
        ORDER BY ta.id DESC
        """

        cursor.execute(query)

        assignments = cursor.fetchall()

        cursor.close()
        connection.close()

        return assignments


    @staticmethod
    def get_assignment_by_id(id):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM teacher_assignments
            WHERE id=%s
            """,
            (id,)
        )

        assignment = cursor.fetchone()

        cursor.close()
        connection.close()

        return assignment


    @staticmethod
    def get_teachers():

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                full_name
            FROM teachers
            WHERE status='Active'
            ORDER BY full_name
        """)

        teachers = cursor.fetchall()

        cursor.close()
        connection.close()

        return teachers


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
    def get_subjects():

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                subject_name
            FROM subjects
            WHERE status='Active'
            ORDER BY subject_name
        """)

        subjects = cursor.fetchall()

        cursor.close()
        connection.close()

        return subjects


    @staticmethod
    def get_admission_years():

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                year
            FROM admission_years
            WHERE status='Active'
            ORDER BY year DESC
        """)

        years = cursor.fetchall()

        cursor.close()
        connection.close()

        return years


    @staticmethod
    def add_assignment(data):

        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
        INSERT INTO teacher_assignments
        (
            teacher_id,
            department_id,
            subject_id,
            admission_year_id,
            semester,
            section,
            academic_year,
            status
        )
        VALUES
        (
            %s,%s,%s,%s,%s,%s,%s,%s
        )
        """

        values = (
            data["teacher_id"],
            data["department_id"],
            data["subject_id"],
            data["admission_year_id"],
            data["semester"],
            data["section"],
            data["academic_year"],
            data["status"]
        )

        cursor.execute(query, values)

        connection.commit()

        cursor.close()
        connection.close()


    @staticmethod
    def update_assignment(data):

        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
        UPDATE teacher_assignments
        SET
            teacher_id=%s,
            department_id=%s,
            subject_id=%s,
            admission_year_id=%s,
            semester=%s,
            section=%s,
            academic_year=%s,
            status=%s
        WHERE id=%s
        """

        values = (
            data["teacher_id"],
            data["department_id"],
            data["subject_id"],
            data["admission_year_id"],
            data["semester"],
            data["section"],
            data["academic_year"],
            data["status"],
            data["id"]
        )

        cursor.execute(query, values)

        connection.commit()

        cursor.close()
        connection.close()


    @staticmethod
    def delete_assignment(id):

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE
            FROM teacher_assignments
            WHERE id=%s
            """,
            (id,)
        )

        connection.commit()

        cursor.close()
        connection.close()
    @staticmethod
    def assignment_exists(data):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT id
        FROM teacher_assignments
        WHERE
            teacher_id=%s
            AND department_id=%s
            AND subject_id=%s
            AND admission_year_id=%s
            AND semester=%s
            AND section=%s
        """

        values = (
            data["teacher_id"],
            data["department_id"],
            data["subject_id"],
            data["admission_year_id"],
            data["semester"],
            data["section"]
        )

        cursor.execute(query, values)

        assignment = cursor.fetchone()

        cursor.close()
        connection.close()

        return assignment


    @staticmethod
    def search_assignments(keyword=""):

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT
            ta.id,
            t.full_name AS teacher_name,
            d.department_name,
            s.subject_name,
            ay.year,
            ta.semester,
            ta.section,
            ta.academic_year,
            ta.status
        FROM teacher_assignments ta
        JOIN teachers t
            ON ta.teacher_id = t.id
        JOIN departments d
            ON ta.department_id = d.id
        JOIN subjects s
            ON ta.subject_id = s.id
        JOIN admission_years ay
            ON ta.admission_year_id = ay.id
        WHERE
            t.full_name LIKE %s
            OR d.department_name LIKE %s
            OR s.subject_name LIKE %s
            OR ta.section LIKE %s
            OR ta.academic_year LIKE %s
        ORDER BY ta.id DESC
        """

        value = "%" + keyword + "%"

        cursor.execute(
            query,
            (value, value, value, value, value)
        )

        assignments = cursor.fetchall()

        cursor.close()
        connection.close()

        return assignments