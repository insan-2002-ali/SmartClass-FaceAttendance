from database.db import get_connection


class AttendanceService:

    def mark_attendance(
        self,
        student_id,
        subject_id,
        teacher_id,
        confidence
    ):

        print("=" * 60)
        print("Attendance")
        print("=" * 60)

        print("Student :", student_id)
        print("Confidence :", confidence)

        return True