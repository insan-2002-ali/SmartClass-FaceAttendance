
import os
from datetime import datetime, timedelta


class AttendanceEngine:
    """
    AI Attendance Database Engine.

    Exactly 3 checks:
        3/3 = Present
        2/3 = Present (default setting)
        1/3 = Absent
        0/3 = Absent

    The minimum required checks are loaded from
    attendance_settings.minimum_present_checks.
    """

    TOTAL_CHECKS = 3

    def __init__(self):

        from database.db import get_connection

        self.connection = get_connection()

        self.cursor = self.connection.cursor(
            dictionary=True
        )

        self.test_mode = (
            os.getenv("ATTENDANCE_TEST_MODE", "0") == "1"
        )

        self.minimum_present_checks = 2

        self.load_attendance_settings()

    # =====================================================
    # LOAD GLOBAL ATTENDANCE SETTINGS
    # =====================================================

    def load_attendance_settings(self):

        self.cursor.execute("""
            SELECT minimum_present_checks
            FROM attendance_settings
            WHERE id = 1
            LIMIT 1
        """)

        settings = self.cursor.fetchone()

        if not settings:
            raise RuntimeError(
                "Global attendance settings not found."
            )

        minimum = int(
            settings["minimum_present_checks"]
        )

        if not 1 <= minimum <= self.TOTAL_CHECKS:
            raise ValueError(
                "minimum_present_checks must be between 1 and 3."
            )

        self.minimum_present_checks = minimum

        print(
            "Minimum successful checks:",
            self.minimum_present_checks
        )

    # =====================================================
    # GET TODAY'S CLASS
    # =====================================================

    def get_today_class(self):

        today = datetime.now().strftime("%A")

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

                ORDER BY cs.start_time, cs.id
                LIMIT 1
            """

            self.cursor.execute(sql)

            return self.cursor.fetchone()

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

            ORDER BY cs.start_time, cs.id
            LIMIT 1
        """

        self.cursor.execute(sql, (today,))

        return self.cursor.fetchone()

    # =====================================================
    # GET STUDENT
    # =====================================================

    def get_student(self, student_number):

        self.cursor.execute("""
            SELECT id, student_id
            FROM students
            WHERE student_id = %s
            LIMIT 1
        """, (student_number,))

        return self.cursor.fetchone()

    # =====================================================
    # GET / CREATE SESSION
    # =====================================================

    def get_or_create_session(
        self,
        attendance_id,
        student_id
    ):

        self.cursor.execute("""
            INSERT IGNORE INTO attendance_sessions
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
            VALUES (%s, %s, NULL, NULL, 0, 0, 0, 'Active')
        """, (attendance_id, student_id))

        self.connection.commit()

        self.cursor.execute("""
            SELECT *
            FROM attendance_sessions
            WHERE attendance_id = %s
              AND student_id = %s
            LIMIT 1
        """, (attendance_id, student_id))

        session = self.cursor.fetchone()

        if not session:
            raise RuntimeError(
                "Could not create or retrieve attendance session."
            )

        return session

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

        if self.test_mode:

            now = datetime.now()

            test_start = now.time()
            test_end = (
                now + timedelta(seconds=1)
            ).time()

            print("TEST ATTENDANCE MODE")
            print(
                "Database attendance time:",
                test_start.strftime("%H:%M:%S")
            )

            try:

                self.cursor.execute("""
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
                    VALUES (%s, %s, %s, %s, %s, 0, 0, 0, 'Open')
                """, (
                    class_id,
                    today,
                    test_start,
                    test_end,
                    teacher_id
                ))

                self.connection.commit()

            except Exception as error:

                self.connection.rollback()

                print("Could not create test attendance:", error)

                return None

            attendance_id = self.cursor.lastrowid

            self.cursor.execute("""
                SELECT *
                FROM attendance
                WHERE id = %s
                LIMIT 1
            """, (attendance_id,))

            return self.cursor.fetchone()

        self.cursor.execute("""
            SELECT *
            FROM attendance
            WHERE class_id = %s
              AND attendance_date = %s
              AND start_time = %s
            ORDER BY id DESC
            LIMIT 1
        """, (class_id, today, start_time))

        existing = self.cursor.fetchone()

        if existing:

            if existing["status"] in ("Completed", "Cancelled"):

                print(
                    "Attendance is already finalized "
                    "for this class today."
                )

                return None

            return existing

        try:

            self.cursor.execute("""
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
                VALUES (%s, %s, %s, %s, %s, 0, 0, 0, 'Open')
            """, (
                class_id,
                today,
                start_time,
                end_time,
                teacher_id
            ))

            self.connection.commit()

        except Exception as error:

            self.connection.rollback()

            print("Could not create attendance:", error)

            # Another worker may have created the same attendance.
            self.cursor.execute("""
                SELECT *
                FROM attendance
                WHERE class_id = %s
                  AND attendance_date = %s
                  AND start_time = %s
                ORDER BY id DESC
                LIMIT 1
            """, (class_id, today, start_time))

            return self.cursor.fetchone()

        attendance_id = self.cursor.lastrowid

        self.cursor.execute("""
            SELECT *
            FROM attendance
            WHERE id = %s
            LIMIT 1
        """, (attendance_id,))

        return self.cursor.fetchone()

    # =====================================================
    # STUDENT ENROLLED
    # =====================================================

    def student_enrolled(
        self,
        student_id,
        teacher_assignment_id
    ):

        self.cursor.execute("""
            SELECT id
            FROM student_enrollments
            WHERE student_id = %s
              AND teacher_assignment_id = %s
              AND status = 'Active'
            LIMIT 1
        """, (student_id, teacher_assignment_id))

        return self.cursor.fetchone()

    # =====================================================
    # GET ONE CHECK RESULT
    # =====================================================

    def get_check_result(
        self,
        attendance_id,
        student_id,
        check_number
    ):

        self.cursor.execute("""
            SELECT *
            FROM attendance_check_results
            WHERE attendance_id = %s
              AND student_id = %s
              AND check_number = %s
            LIMIT 1
        """, (
            attendance_id,
            student_id,
            check_number
        ))

        return self.cursor.fetchone()

    # =====================================================
    # RECORD CHECK
    # =====================================================

    def record_check(
        self,
        attendance_id,
        student_id,
        check_number,
        status="Present",
        confidence=None,
        check_time=None
    ):

        if check_time is None:
            check_time = datetime.now()

        try:
            check_number = int(check_number)
        except (TypeError, ValueError):
            check_number = 0

        if not 1 <= check_number <= self.TOTAL_CHECKS:

            return {
                "success": False,
                "duplicate": False,
                "message": "Invalid check number."
            }

        if status not in ("Present", "Missed"):
            status = "Missed"

        # Check for an existing result first.
        existing = self.get_check_result(
            attendance_id,
            student_id,
            check_number
        )

        if existing:

            return {
                "success": False,
                "duplicate": True,
                "message": "Already counted for this check.",
                "check_number": check_number
            }

        try:

            self.cursor.execute("""
                INSERT INTO attendance_check_results
                (
                    attendance_id,
                    student_id,
                    check_number,
                    check_time,
                    status,
                    confidence_score
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                attendance_id,
                student_id,
                check_number,
                check_time,
                status,
                confidence
            ))

            self.connection.commit()

            return {
                "success": True,
                "duplicate": False,
                "message": "Check recorded.",
                "check_number": check_number
            }

        except Exception as error:

            self.connection.rollback()

            # The UNIQUE constraint also protects against
            # simultaneous duplicate inserts.
            existing = self.get_check_result(
                attendance_id,
                student_id,
                check_number
            )

            if existing:

                return {
                    "success": False,
                    "duplicate": True,
                    "message": "Already counted for this check.",
                    "check_number": check_number
                }

            print("Could not record check:", error)

            return {
                "success": False,
                "duplicate": False,
                "message": str(error)
            }

    # =====================================================
    # GET STUDENT CHECK COUNT
    # =====================================================

    def get_student_check_count(
        self,
        attendance_id,
        student_id
    ):

        self.cursor.execute("""
            SELECT COUNT(DISTINCT check_number) AS total
            FROM attendance_check_results
            WHERE attendance_id = %s
              AND student_id = %s
              AND status = 'Present'
              AND check_number BETWEEN 1 AND 3
        """, (attendance_id, student_id))

        result = self.cursor.fetchone()

        return int(result["total"]) if result else 0

    # =====================================================
    # GET ALL STUDENT CHECKS
    # =====================================================

    def get_student_checks(
        self,
        attendance_id,
        student_id
    ):

        self.cursor.execute("""
            SELECT
                check_number,
                check_time,
                status,
                confidence_score
            FROM attendance_check_results
            WHERE attendance_id = %s
              AND student_id = %s
            ORDER BY check_number ASC
        """, (attendance_id, student_id))

        return self.cursor.fetchall()

    # =====================================================
    # CALCULATE FINAL CHECK STATUS
    # =====================================================

    def calculate_check_status(
        self,
        attendance_id,
        student_id
    ):

        present_checks = self.get_student_check_count(
            attendance_id,
            student_id
        )

        status = (
            "Present"
            if present_checks >= self.minimum_present_checks
            else "Absent"
        )

        percentage = (
            present_checks / self.TOTAL_CHECKS
        ) * 100

        return {
            "checks": present_checks,
            "total_checks": self.TOTAL_CHECKS,
            "minimum_required": self.minimum_present_checks,
            "percentage": round(percentage, 2),
            "status": status
        }

    # =====================================================
    # FINALIZE CHECK ATTENDANCE
    # =====================================================

    def finalize_check_attendance(
        self,
        attendance_id,
        student_ids
    ):

        present_students = 0
        absent_students = 0

        student_ids = list(dict.fromkeys(student_ids))

        try:

            for student_id in student_ids:

                result = self.calculate_check_status(
                    attendance_id,
                    student_id
                )

                status = result["status"]
                percentage = result["percentage"]

                self.get_or_create_session(
                    attendance_id,
                    student_id
                )

                self.cursor.execute("""
                    UPDATE attendance_sessions
                    SET
                        total_present_seconds = 0,
                        total_absent_seconds = 0,
                        attendance_percentage = %s,
                        status = %s
                    WHERE attendance_id = %s
                      AND student_id = %s
                """, (
                    percentage,
                    status,
                    attendance_id,
                    student_id
                ))

                self.cursor.execute("""
                    SELECT id
                    FROM attendance_details
                    WHERE attendance_id = %s
                      AND student_id = %s
                    LIMIT 1
                """, (attendance_id, student_id))

                detail_exists = self.cursor.fetchone()

                self.cursor.execute("""
                    SELECT MAX(confidence_score) AS confidence
                    FROM attendance_check_results
                    WHERE attendance_id = %s
                      AND student_id = %s
                      AND status = 'Present'
                """, (attendance_id, student_id))

                confidence_result = self.cursor.fetchone()

                confidence = (
                    confidence_result["confidence"]
                    if confidence_result
                    else None
                )

                if detail_exists:

                    self.cursor.execute("""
                        UPDATE attendance_details
                        SET
                            attendance_status = %s,
                            confidence_score = %s,
                            remarks = %s
                        WHERE attendance_id = %s
                          AND student_id = %s
                    """, (
                        status,
                        confidence,
                        (
                            f"{result['checks']}/"
                            f"{self.TOTAL_CHECKS} checks"
                        ),
                        attendance_id,
                        student_id
                    ))

                else:

                    self.cursor.execute("""
                        INSERT INTO attendance_details
                        (
                            attendance_id,
                            student_id,
                            attendance_time,
                            attendance_status,
                            confidence_score,
                            remarks
                        )
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        attendance_id,
                        student_id,
                        datetime.now(),
                        status,
                        confidence,
                        (
                            f"{result['checks']}/"
                            f"{self.TOTAL_CHECKS} checks"
                        )
                    ))

                if status == "Present":
                    present_students += 1
                else:
                    absent_students += 1

            total_students = len(student_ids)

            self.cursor.execute("""
                UPDATE attendance
                SET
                    total_students = %s,
                    present_students = %s,
                    absent_students = %s,
                    status = 'Completed',
                    end_time = %s
                WHERE id = %s
            """, (
                total_students,
                present_students,
                absent_students,
                datetime.now().time(),
                attendance_id
            ))

            self.connection.commit()

        except Exception:

            self.connection.rollback()
            raise

        return {
            "total_students": total_students,
            "present_students": present_students,
            "absent_students": absent_students
        }


    
    # =====================================================
    # CANCEL OPEN ATTENDANCE
    # =====================================================

    def cancel_attendance(self, attendance_id):

        if not attendance_id:
            return False

        try:

            self.cursor.execute("""
                UPDATE attendance
                SET
                    status = 'Cancelled',
                    end_time = %s
                WHERE id = %s
                  AND status = 'Open'
            """, (
                datetime.now().time(),
                attendance_id
            ))

            self.connection.commit()

            if self.cursor.rowcount > 0:

                print(
                    f"Attendance {attendance_id} cancelled."
                )

                return True

            return False

        except Exception:

            self.connection.rollback()

            raise


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

        self.cursor.execute("""
            INSERT INTO attendance_presence_logs
            (
                attendance_id,
                student_id,
                check_time,
                status
            )
            VALUES (%s, %s, %s, %s)
        """, (
            attendance_id,
            student_id,
            check_time,
            status
        ))

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

        self.cursor.execute("""
            SELECT *
            FROM attendance_presence_logs
            WHERE attendance_id = %s
              AND student_id = %s
            ORDER BY check_time DESC, id DESC
            LIMIT 1
        """, (attendance_id, student_id))

        return self.cursor.fetchone()

    # =====================================================
    # GET PRESENCE LOGS
    # =====================================================

    def get_presence_logs(
        self,
        attendance_id,
        student_id
    ):

        self.cursor.execute("""
            SELECT *
            FROM attendance_presence_logs
            WHERE attendance_id = %s
              AND student_id = %s
            ORDER BY check_time ASC, id ASC
        """, (attendance_id, student_id))

        return self.cursor.fetchall()

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

        self.cursor.execute("""
            UPDATE attendance_sessions
            SET
                first_seen = %s,
                last_seen = %s,
                status = 'Active'
            WHERE attendance_id = %s
              AND student_id = %s
              AND first_seen IS NULL
        """, (
            seen_time,
            seen_time,
            attendance_id,
            student_id
        ))

        self.connection.commit()

        if self.cursor.rowcount == 0:
            return False

        self.add_presence_log(
            attendance_id,
            student_id,
            seen_time,
            "Present"
        )

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

        session = self.get_or_create_session(
            attendance_id,
            student_id
        )

        if session["first_seen"] is None:

            return self.mark_first_seen(
                attendance_id,
                student_id,
                seen_time
            )

        self.cursor.execute("""
            UPDATE attendance_sessions
            SET last_seen = %s
            WHERE attendance_id = %s
              AND student_id = %s
        """, (
            seen_time,
            attendance_id,
            student_id
        ))

        self.connection.commit()

        return True

    # =====================================================
    # MARK DETECTED
    # =====================================================

    def mark_detected(
        self,
        attendance_id,
        student_number,
        seen_time=None,
        confidence=None
    ):

        if seen_time is None:
            seen_time = datetime.now()

        student = self.get_student(student_number)

        if student is None:

            return {
                "success": False,
                "message": "Student not found"
            }

        student_id = student["id"]

        session = self.get_or_create_session(
            attendance_id,
            student_id
        )

        if session["first_seen"] is None:

            self.mark_first_seen(
                attendance_id,
                student_id,
                seen_time
            )

            return {
                "success": True,
                "message": "ENTRY",
                "student_id": student_id
            }

        last_log = self.get_last_presence_log(
            attendance_id,
            student_id
        )

        if (
            last_log is not None
            and last_log["status"] == "Exit"
        ):

            self.add_presence_log(
                attendance_id,
                student_id,
                seen_time,
                "Return"
            )

            self.update_last_seen(
                attendance_id,
                student_id,
                seen_time
            )

            return {
                "success": True,
                "message": "RETURN",
                "student_id": student_id
            }

        self.update_last_seen(
            attendance_id,
            student_id,
            seen_time
        )

        return {
            "success": True,
            "message": "PRESENT",
            "student_id": student_id
        }

    # =====================================================
    # MARK EXIT
    # =====================================================

    def mark_exit(
        self,
        attendance_id,
        student_id,
        exit_time=None
    ):

        if exit_time is None:
            exit_time = datetime.now()

        last_log = self.get_last_presence_log(
            attendance_id,
            student_id
        )

        if last_log is None:
            return False

        if last_log["status"] == "Exit":
            return False

        if last_log["status"] not in ("Present", "Return"):
            return False

        self.add_presence_log(
            attendance_id,
            student_id,
            exit_time,
            "Exit"
        )

        self.cursor.execute("""
            UPDATE attendance_sessions
            SET last_seen = %s
            WHERE attendance_id = %s
              AND student_id = %s
        """, (
            exit_time,
            attendance_id,
            student_id
        ))

        self.connection.commit()

        return True

    # =====================================================
    # CALCULATE INTERVAL
    # =====================================================

    def calculate_interval(
        self,
        start,
        end,
        class_start,
        class_end,
        break_start,
        break_end
    ):

        if (
            start is None
            or end is None
            or end <= start
        ):
            return 0

        start = max(start, class_start)
        end = min(end, class_end)

        if end <= start:
            return 0

        total_seconds = (
            end - start
        ).total_seconds()

        if (
            break_start is not None
            and break_end is not None
        ):

            overlap_start = max(start, break_start)
            overlap_end = min(end, break_end)

            if overlap_end > overlap_start:

                total_seconds -= (
                    overlap_end - overlap_start
                ).total_seconds()

        return max(0, total_seconds)

    # =====================================================
    # CALCULATE PRESENT SECONDS
    # =====================================================

    def calculate_present_seconds(
        self,
        attendance_id,
        student_id,
        class_start,
        class_end,
        break_start,
        break_end
    ):

        logs = self.get_presence_logs(
            attendance_id,
            student_id
        )

        if not logs:
            return 0

        total_seconds = 0
        current_entry = None

        for log in logs:

            status = log["status"]
            log_time = log["check_time"]

            if status in ("Present", "Return"):

                if current_entry is None:
                    current_entry = log_time

            elif status == "Exit":

                if current_entry is not None:

                    total_seconds += self.calculate_interval(
                        current_entry,
                        log_time,
                        class_start,
                        class_end,
                        break_start,
                        break_end
                    )

                    current_entry = None

        if current_entry is not None:

            total_seconds += self.calculate_interval(
                current_entry,
                class_end,
                class_start,
                class_end,
                break_start,
                break_end
            )

        return max(0, int(total_seconds))

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
