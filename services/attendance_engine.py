import os
from datetime import datetime


class AttendanceEngine:
    """
    Attendance database engine.

    Attendance rule:
        - Exactly 4 camera checks.
        - Student must be successfully recognized
          in at least 3 DIFFERENT checks.
        - 3/4 or 4/4 = Present.
        - 0/4, 1/4 or 2/4 = Absent.
        - Same check can only count once.
    """

    TOTAL_CHECKS = 4
    MINIMUM_PRESENT_CHECKS = 3

    def __init__(self):
        from database.db import get_connection

        self.connection = get_connection()
        self.cursor = self.connection.cursor(dictionary=True)

        self.test_mode = (
            os.getenv("ATTENDANCE_TEST_MODE", "0") == "1"
        )

    # =====================================================
    # GET TODAY'S CLASS
    # =====================================================

    def get_today_class(self):

        today = datetime.now().strftime("%A")

        # =================================================
        # TEST MODE
        #
        # Ignore weekday.
        # Pick first active schedule.
        # =================================================

        if self.test_mode:

            sql = """
            SELECT
                cs.*,
                c.class_code,
                c.class_name,
                c.teacher_id

            FROM class_schedules cs

            INNER JOIN classes c
                ON c.id = cs.class_id

            WHERE cs.status = 'Active'

            AND c.status = 'Active'

            ORDER BY
                cs.start_time ASC,
                cs.id ASC

            LIMIT 1
            """

            self.cursor.execute(sql)

            return self.cursor.fetchone()

        # =================================================
        # PRODUCTION MODE
        # =================================================

        sql = """
        SELECT
            cs.*,
            c.class_code,
            c.class_name,
            c.teacher_id

        FROM class_schedules cs

        INNER JOIN classes c
            ON c.id = cs.class_id

        WHERE cs.day_of_week = %s

        AND cs.status = 'Active'

        AND c.status = 'Active'

        ORDER BY cs.start_time ASC

        LIMIT 1
        """

        self.cursor.execute(
            sql,
            (today,)
        )

        return self.cursor.fetchone()

    # =====================================================
    # GET STUDENT
    # =====================================================

    def get_student(self, student_number):

        sql = """
        SELECT
            id,
            student_id

        FROM students

        WHERE student_id = %s

        LIMIT 1
        """

        self.cursor.execute(
            sql,
            (student_number,)
        )

        return self.cursor.fetchone()

    # =====================================================
    # GET / CREATE SESSION
    # =====================================================

    def get_or_create_session(
        self,
        attendance_id,
        student_id
    ):

        sql = """
        SELECT *

        FROM attendance_sessions

        WHERE attendance_id = %s

        AND student_id = %s

        LIMIT 1
        """

        self.cursor.execute(
            sql,
            (
                attendance_id,
                student_id
            )
        )

        session = self.cursor.fetchone()

        if session:
            return session

        sql = """
        INSERT INTO attendance_sessions
        (
            attendance_id,
            student_id,
            first_seen,
            last_seen,
            total_present_seconds,
            total_absent_seconds,
            attendance_percentage,
            status
        )

        VALUES
        (
            %s,
            %s,
            NULL,
            NULL,
            0,
            0,
            0,
            'Active'
        )
        """

        self.cursor.execute(
            sql,
            (
                attendance_id,
                student_id
            )
        )

        self.connection.commit()

        self.cursor.execute(
            """
            SELECT *

            FROM attendance_sessions

            WHERE attendance_id = %s

            AND student_id = %s

            LIMIT 1
            """,
            (
                attendance_id,
                student_id
            )
        )

        return self.cursor.fetchone()

    # =====================================================
    # CREATE ATTENDANCE
    # =====================================================

    def create_attendance(
        self,
        class_id,
        teacher_id,
        start_time,
        end_time
    ):

        today = datetime.now().date()

        # =================================================
        # TEST MODE
        # =================================================

        if self.test_mode:

            now = datetime.now()

            test_start = now.time()

            test_end = now.time()

            print()
            print(
                "TEST ATTENDANCE MODE"
            )

            print(
                "Database attendance time:",
                test_start.strftime("%H:%M:%S")
            )

            sql = """
            INSERT INTO attendance
            (
                class_id,
                attendance_date,
                start_time,
                end_time,
                taken_by,
                total_students,
                present_students,
                absent_students,
                status
            )

            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                0,
                0,
                0,
                'Open'
            )
            """

            try:

                self.cursor.execute(
                    sql,
                    (
                        class_id,
                        today,
                        test_start,
                        test_end,
                        teacher_id
                    )
                )

                self.connection.commit()

            except Exception as error:

                self.connection.rollback()

                print(
                    "Could not create test attendance:"
                )

                print(error)

                return None

            attendance_id = self.cursor.lastrowid

            self.cursor.execute(
                """
                SELECT *

                FROM attendance

                WHERE id = %s

                LIMIT 1
                """,
                (attendance_id,)
            )

            return self.cursor.fetchone()

        # =================================================
        # PRODUCTION MODE
        # =================================================

        sql = """
        SELECT *

        FROM attendance

        WHERE class_id = %s

        AND attendance_date = %s

        AND start_time = %s

        ORDER BY id DESC

        LIMIT 1
        """

        self.cursor.execute(
            sql,
            (
                class_id,
                today,
                start_time
            )
        )

        existing = self.cursor.fetchone()

        if existing:

            if existing["status"] == "Completed":

                print()
                print(
                    "Attendance already completed "
                    "for this class today."
                )

                print(
                    f"Attendance ID : {existing['id']}"
                )

                return None

            return existing

        sql = """
        INSERT INTO attendance
        (
            class_id,
            attendance_date,
            start_time,
            end_time,
            taken_by,
            total_students,
            present_students,
            absent_students,
            status
        )

        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            0,
            0,
            0,
            'Open'
        )
        """

        try:

            self.cursor.execute(
                sql,
                (
                    class_id,
                    today,
                    start_time,
                    end_time,
                    teacher_id
                )
            )

            self.connection.commit()

        except Exception as error:

            self.connection.rollback()

            print(
                "Could not create attendance:"
            )

            print(error)

            return None

        attendance_id = self.cursor.lastrowid

        self.cursor.execute(
            """
            SELECT *

            FROM attendance

            WHERE id = %s

            LIMIT 1
            """,
            (attendance_id,)
        )

        return self.cursor.fetchone()

    # =====================================================
    # STUDENT ENROLLED
    # =====================================================

    def student_enrolled(
        self,
        student_id,
        teacher_assignment_id
    ):

        sql = """
        SELECT *

        FROM student_enrollments

        WHERE student_id = %s

        AND teacher_assignment_id = %s

        AND status = 'Active'

        LIMIT 1
        """

        self.cursor.execute(
            sql,
            (
                student_id,
                teacher_assignment_id
            )
        )

        return self.cursor.fetchone()

    # =====================================================
    # ADD PRESENCE LOG
    # =====================================================

    def add_presence_log(
        self,
        attendance_id,
        student_id,
        check_time,
        status
    ):

        sql = """
        INSERT INTO attendance_presence_logs
        (
            attendance_id,
            student_id,
            check_time,
            status
        )

        VALUES
        (
            %s,
            %s,
            %s,
            %s
        )
        """

        self.cursor.execute(
            sql,
            (
                attendance_id,
                student_id,
                check_time,
                status
            )
        )

        self.connection.commit()

        return True

    # =====================================================
    # GET LAST PRESENCE LOG
    # =====================================================

    def get_last_presence_log(
        self,
        attendance_id,
        student_id
    ):

        sql = """
        SELECT *

        FROM attendance_presence_logs

        WHERE attendance_id = %s

        AND student_id = %s

        ORDER BY check_time DESC, id DESC

        LIMIT 1
        """

        self.cursor.execute(
            sql,
            (
                attendance_id,
                student_id
            )
        )

        return self.cursor.fetchone()

    # =====================================================
    # GET PRESENCE LOGS
    # =====================================================

    def get_presence_logs(
        self,
        attendance_id,
        student_id
    ):

        sql = """
        SELECT *

        FROM attendance_presence_logs

        WHERE attendance_id = %s

        AND student_id = %s

        ORDER BY check_time ASC, id ASC
        """

        self.cursor.execute(
            sql,
            (
                attendance_id,
                student_id
            )
        )

        return self.cursor.fetchall()

    # =====================================================
    # RECORD CHECK
    #
    # IMPORTANT:
    # One successful recognition per check_number.
    #
    # Example:
    #
    # Check 1 -> Present
    # Check 2 -> Present
    # Check 3 -> Present
    #
    # = 3/4 -> Present
    # =====================================================

    def record_check(
        self,
        attendance_id,
        student_number,
        check_number,
        check_time=None,
        confidence=None
    ):

        if check_time is None:
            check_time = datetime.now()

        # =================================================
        # VALIDATE CHECK NUMBER
        # =================================================

        if check_number < 1 or check_number > self.TOTAL_CHECKS:

            return {
                "success": False,
                "message": "Invalid check number"
            }

        # =================================================
        # FIND STUDENT
        # =================================================

        student = self.get_student(
            student_number
        )

        if student is None:

            return {
                "success": False,
                "message": "Student not found"
            }

        student_id = student["id"]

        # =================================================
        # CHECK IF ALREADY COUNTED
        # =================================================

        sql = """
        SELECT
            id,
            status

        FROM attendance_check_results

        WHERE attendance_id = %s

        AND student_id = %s

        AND check_number = %s

        LIMIT 1
        """

        self.cursor.execute(
            sql,
            (
                attendance_id,
                student_id,
                check_number
            )
        )

        existing = self.cursor.fetchone()

        # =================================================
        # DO NOT COUNT SAME CHECK TWICE
        # =================================================

        if existing:

            return {
                "success": True,
                "message": "Already recorded",
                "counted": existing["status"] == "Present",
                "student_id": student_id
            }

        # =================================================
        # INSERT SUCCESSFUL CHECK
        # =================================================

        sql = """
        INSERT INTO attendance_check_results
        (
            attendance_id,
            student_id,
            check_number,
            check_time,
            status,
            confidence_score
        )

        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            'Present',
            %s
        )
        """

        self.cursor.execute(
            sql,
            (
                attendance_id,
                student_id,
                check_number,
                check_time,
                confidence
            )
        )

        self.connection.commit()

        # =================================================
        # COUNT SUCCESSFUL CHECKS
        # =================================================

        sql = """
        SELECT COUNT(*) AS total

        FROM attendance_check_results

        WHERE attendance_id = %s

        AND student_id = %s

        AND status = 'Present'
        """

        self.cursor.execute(
            sql,
            (
                attendance_id,
                student_id
            )
        )

        result = self.cursor.fetchone()

        successful_checks = (
            result["total"]
            if result
            else 0
        )

        # =================================================
        # FINAL ATTENDANCE DECISION
        # =================================================

        attendance_status = (
            "Present"
            if successful_checks >= self.MINIMUM_PRESENT_CHECKS
            else "Absent"
        )

        return {
            "success": True,
            "message": "Check recorded",
            "counted": True,
            "student_id": student_id,
            "check_number": check_number,
            "successful_checks": successful_checks,
            "required_checks": self.MINIMUM_PRESENT_CHECKS,
            "attendance_status": attendance_status
        }

    # =====================================================
    # MARK FIRST SEEN
    # =====================================================

    def mark_first_seen(
        self,
        attendance_id,
        student_id,
        seen_time=None
    ):

        if seen_time is None:
            seen_time = datetime.now()

        session = self.get_or_create_session(
            attendance_id,
            student_id
        )

        if session["first_seen"] is not None:
            return False

        sql = """
        UPDATE attendance_sessions

        SET
            first_seen = %s,
            last_seen = %s,
            status = 'Active'

        WHERE attendance_id = %s

        AND student_id = %s
        """

        self.cursor.execute(
            sql,
            (
                seen_time,
                seen_time,
                attendance_id,
                student_id
            )
        )

        self.connection.commit()

        return True

    # =====================================================
    # UPDATE LAST SEEN
    # =====================================================

    def update_last_seen(
        self,
        attendance_id,
        student_id,
        seen_time=None
    ):

        if seen_time is None:
            seen_time = datetime.now()

        sql = """
        UPDATE attendance_sessions

        SET last_seen = %s

        WHERE attendance_id = %s

        AND student_id = %s
        """

        self.cursor.execute(
            sql,
            (
                seen_time,
                attendance_id,
                student_id
            )
        )

        self.connection.commit()

        return True

    # =====================================================
    # FINALIZE SESSION
    #
    # Final decision is based on 4 checks.
    # =====================================================

    def finalize_session_by_checks(
        self,
        attendance_id,
        student_id
    ):

        sql = """
        SELECT COUNT(*) AS total

        FROM attendance_check_results

        WHERE attendance_id = %s

        AND student_id = %s

        AND status = 'Present'
        """

        self.cursor.execute(
            sql,
            (
                attendance_id,
                student_id
            )
        )

        result = self.cursor.fetchone()

        successful_checks = (
            result["total"]
            if result
            else 0
        )

        if successful_checks >= self.MINIMUM_PRESENT_CHECKS:

            status = "Present"

        else:

            status = "Absent"

        sql = """
        UPDATE attendance_sessions

        SET
            attendance_percentage = %s,
            status = %s

        WHERE attendance_id = %s

        AND student_id = %s
        """

        percentage = (
            successful_checks
            /
            self.TOTAL_CHECKS
        ) * 100

        self.cursor.execute(
            sql,
            (
                round(percentage, 2),
                status,
                attendance_id,
                student_id
            )
        )

        self.connection.commit()

        return status

    # =====================================================
    # FINALIZE ATTENDANCE
    # =====================================================

    def finalize_attendance(
        self,
        attendance_id,
        total_students
    ):

        # =================================================
        # FINALIZE ALL STUDENTS
        # =================================================

        self.cursor.execute(
            """
            SELECT student_id

            FROM attendance_sessions

            WHERE attendance_id = %s
            """,
            (attendance_id,)
        )

        students = self.cursor.fetchall()

        for student in students:

            self.finalize_session_by_checks(
                attendance_id,
                student["student_id"]
            )

        # =================================================
        # PRESENT COUNT
        # =================================================

        self.cursor.execute(
            """
            SELECT COUNT(*) AS total

            FROM attendance_sessions

            WHERE attendance_id = %s

            AND status = 'Present'
            """,
            (attendance_id,)
        )

        result = self.cursor.fetchone()

        present_students = (
            result["total"]
            if result
            else 0
        )

        # =================================================
        # ABSENT COUNT
        # =================================================

        self.cursor.execute(
            """
            SELECT COUNT(*) AS total

            FROM attendance_sessions

            WHERE attendance_id = %s

            AND status = 'Absent'
            """,
            (attendance_id,)
        )

        result = self.cursor.fetchone()

        absent_students = (
            result["total"]
            if result
            else 0
        )

        # =================================================
        # UPDATE ATTENDANCE
        # =================================================

        sql = """
        UPDATE attendance

        SET
            total_students = %s,
            present_students = %s,
            absent_students = %s,
            status = 'Completed'

        WHERE id = %s
        """

        self.cursor.execute(
            sql,
            (
                total_students,
                present_students,
                absent_students,
                attendance_id
            )
        )

        self.connection.commit()

        return True

    # =====================================================
    # CLOSE
    # =====================================================

    def close(self):

        try:
            self.cursor.close()
        except Exception:
            pass

        try:
            self.connection.close()
        except Exception:
            pass