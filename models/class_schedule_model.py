
from database.db import get_connection


class ClassScheduleModel:

    # =====================================================
    # GET ACTIVE CLASSES
    # =====================================================

    @staticmethod
    def get_all_classes():

        connection = get_connection()
        cursor = None

        try:
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT
                    c.id,
                    c.class_code,
                    c.class_name,
                    c.section,
                    c.semester,
                    c.academic_year,
                    c.status,

                    s.subject_name,
                    t.full_name AS teacher_name,

                    d.department_name,
                    p.degree,
                    p.program_name

                FROM classes c

                INNER JOIN subjects s
                    ON c.subject_id = s.id

                INNER JOIN teachers t
                    ON c.teacher_id = t.id

                LEFT JOIN departments d
                    ON c.department_id = d.id

                LEFT JOIN programs p
                    ON c.program_id = p.id

                WHERE c.status = 'Active'

                ORDER BY
                    c.academic_year DESC,
                    p.degree,
                    d.department_name,
                    c.class_code
            """

            cursor.execute(query)

            return cursor.fetchall()

        finally:
            if cursor:
                cursor.close()

            connection.close()

    # =====================================================
    # GET ALL CLASS SCHEDULES
    # =====================================================

    @staticmethod
    def get_all_schedules():

        connection = get_connection()
        cursor = None

        try:
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT
                    cs.id,
                    cs.class_id,
                    cs.day_of_week,
                    cs.start_time,
                    cs.end_time,
                    cs.room_no,
                    cs.building,
                    cs.status,
                    cs.created_at,

                    TIMESTAMPDIFF(
                        MINUTE,
                        cs.start_time,
                        cs.end_time
                    ) AS duration_minutes,

                    c.class_code,
                    c.class_name,
                    c.section,
                    c.semester,
                    c.academic_year,

                    s.subject_name,
                    t.full_name AS teacher_name,

                    d.department_name,
                    p.degree,
                    p.program_name

                FROM class_schedules cs

                INNER JOIN classes c
                    ON cs.class_id = c.id

                INNER JOIN subjects s
                    ON c.subject_id = s.id

                INNER JOIN teachers t
                    ON c.teacher_id = t.id

                LEFT JOIN departments d
                    ON c.department_id = d.id

                LEFT JOIN programs p
                    ON c.program_id = p.id

                ORDER BY
                    FIELD(
                        cs.day_of_week,
                        'Sunday',
                        'Monday',
                        'Tuesday',
                        'Wednesday',
                        'Thursday',
                        'Friday',
                        'Saturday'
                    ),
                    cs.start_time,
                    cs.id
            """

            cursor.execute(query)

            return cursor.fetchall()

        finally:
            if cursor:
                cursor.close()

            connection.close()

    # =====================================================
    # GET SCHEDULE BY ID
    # =====================================================

    @staticmethod
    def get_schedule_by_id(schedule_id):

        connection = get_connection()
        cursor = None

        try:
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT
                    cs.*,

                    TIMESTAMPDIFF(
                        MINUTE,
                        cs.start_time,
                        cs.end_time
                    ) AS duration_minutes,

                    c.class_code,
                    c.class_name,
                    c.section,
                    c.semester,
                    c.academic_year,

                    s.subject_name,
                    t.full_name AS teacher_name,

                    d.department_name,
                    p.degree,
                    p.program_name

                FROM class_schedules cs

                INNER JOIN classes c
                    ON cs.class_id = c.id

                INNER JOIN subjects s
                    ON c.subject_id = s.id

                INNER JOIN teachers t
                    ON c.teacher_id = t.id

                LEFT JOIN departments d
                    ON c.department_id = d.id

                LEFT JOIN programs p
                    ON c.program_id = p.id

                WHERE cs.id = %s
                LIMIT 1
            """

            cursor.execute(query, (schedule_id,))

            return cursor.fetchone()

        finally:
            if cursor:
                cursor.close()

            connection.close()

    # =====================================================
    # ADD SCHEDULE
    # =====================================================

    @staticmethod
    def add_schedule(data):

        connection = get_connection()
        cursor = None

        try:
            cursor = connection.cursor()

            query = """
                INSERT INTO class_schedules
                (
                    class_id,
                    day_of_week,
                    start_time,
                    end_time,
                    break_start,
                    break_end,
                    room_no,
                    building,
                    status
                )
                VALUES (
                    %s, %s, %s, %s,
                    NULL, NULL,
                    %s, %s, %s
                )
            """

            values = (
                data["class_id"],
                data["day_of_week"],
                data["start_time"],
                data["end_time"],
                data.get("room_no") or None,
                data.get("building") or None,
                data.get("status", "Active")
            )

            cursor.execute(query, values)

            connection.commit()

            return cursor.lastrowid

        except Exception:
            connection.rollback()
            raise

        finally:
            if cursor:
                cursor.close()

            connection.close()

    # =====================================================
    # UPDATE SCHEDULE
    # =====================================================

    @staticmethod
    def update_schedule(schedule_id, data):

        connection = get_connection()
        cursor = None

        try:
            cursor = connection.cursor()

            query = """
                UPDATE class_schedules

                SET
                    class_id = %s,
                    day_of_week = %s,
                    start_time = %s,
                    end_time = %s,
                    break_start = NULL,
                    break_end = NULL,
                    room_no = %s,
                    building = %s,
                    status = %s

                WHERE id = %s
            """

            values = (
                data["class_id"],
                data["day_of_week"],
                data["start_time"],
                data["end_time"],
                data.get("room_no") or None,
                data.get("building") or None,
                data.get("status", "Active"),
                schedule_id
            )

            cursor.execute(query, values)

            connection.commit()

            return cursor.rowcount

        except Exception:
            connection.rollback()
            raise

        finally:
            if cursor:
                cursor.close()

            connection.close()

    # =====================================================
    # DELETE SCHEDULE
    # =====================================================

    @staticmethod
    def delete_schedule(schedule_id):

        connection = get_connection()
        cursor = None

        try:
            cursor = connection.cursor()

            cursor.execute("""
                DELETE FROM class_schedules
                WHERE id = %s
            """, (schedule_id,))

            connection.commit()

            return cursor.rowcount

        except Exception:
            connection.rollback()
            raise

        finally:
            if cursor:
                cursor.close()

            connection.close()

    # =====================================================
    # GET ACTIVE SCHEDULES FOR A DAY
    # =====================================================

    @staticmethod
    def get_active_schedules_for_day(day):

        connection = get_connection()
        cursor = None

        try:
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT
                    cs.*,
                    c.class_code,
                    c.class_name,
                    c.teacher_id,
                    c.department_id,
                    c.program_id,
                    c.academic_year,
                    s.subject_name,
                    d.department_name

                FROM class_schedules cs

                INNER JOIN classes c
                    ON cs.class_id = c.id

                INNER JOIN subjects s
                    ON c.subject_id = s.id

                LEFT JOIN departments d
                    ON c.department_id = d.id

                WHERE cs.day_of_week = %s
                  AND cs.status = 'Active'
                  AND c.status = 'Active'

                ORDER BY
                    cs.start_time,
                    cs.id
            """

            cursor.execute(query, (day,))

            return cursor.fetchall()

        finally:
            if cursor:
                cursor.close()

            connection.close()
