
from datetime import datetime, timedelta, time as dt_time

from database.db import get_connection


class ClassController:

    def __init__(self, schedule, settings=None):

        self.schedule = schedule

        # Load global settings
        self.settings = (
            settings
            if settings is not None
            else self._load_global_settings()
        )

        if not self.settings:
            raise RuntimeError(
                "Global attendance settings are missing."
            )

        # Class time
        self.class_start = self._to_datetime(
            schedule["start_time"]
        )

        self.class_end = self._to_datetime(
            schedule["end_time"]
        )

        if self.class_end <= self.class_start:
            raise ValueError(
                "Class end time must be after class start time."
            )

        self.duration_minutes = int(
            (
                self.class_end - self.class_start
            ).total_seconds() // 60
        )

        # Preparation time
        preparation_minutes = int(
            self.settings["preparation_minutes"]
        )

        if preparation_minutes < 0:
            raise ValueError(
                "Preparation minutes cannot be negative."
            )

        self.camera_start = (
            self.class_start
            - timedelta(minutes=preparation_minutes)
        )

        # Break configuration
        break_start_min = int(
            self.settings["break_start_min"]
        )

        break_end_min = int(
            self.settings["break_end_min"]
        )

        self._validate_window(
            break_start_min,
            break_end_min,
            "Break"
        )

        self.break_start = (
            self.class_start
            + timedelta(minutes=break_start_min)
        )

        self.break_end = (
            self.class_start
            + timedelta(minutes=break_end_min)
        )

        # Minimum successful checks
        self.minimum_present_checks = int(
            self.settings["minimum_present_checks"]
        )

        if not 1 <= self.minimum_present_checks <= 3:
            raise ValueError(
                "Minimum present checks must be between 1 and 3."
            )

        # Validate the complete attendance timeline
        self._validate_attendance_timeline()

    # =================================================
    # LOAD GLOBAL SETTINGS
    # =================================================

    def _load_global_settings(self):

        connection = None
        cursor = None

        try:

            connection = get_connection()

            cursor = connection.cursor(
                dictionary=True
            )

            cursor.execute("""
                SELECT *
                FROM attendance_settings
                WHERE id = 1
                LIMIT 1
            """)

            settings = cursor.fetchone()

            if not settings:
                raise RuntimeError(
                    "Attendance settings row with id=1 not found."
                )

            return settings

        finally:

            if cursor is not None:
                cursor.close()

            if connection is not None:
                connection.close()

    # =================================================
    # CONVERT MYSQL TIME TO DATETIME
    # =================================================

    def _to_datetime(self, value):

        if value is None:
            raise ValueError(
                "Class start/end time cannot be empty."
            )

        today = datetime.now().date()

        if isinstance(value, timedelta):

            midnight = datetime.combine(
                today,
                dt_time(0, 0)
            )

            return midnight + value

        if isinstance(value, datetime):
            return value

        if isinstance(value, dt_time):

            return datetime.combine(
                today,
                value
            )

        if isinstance(value, str):

            for time_format in (
                "%H:%M:%S",
                "%H:%M"
            ):

                try:

                    parsed = datetime.strptime(
                        value,
                        time_format
                    ).time()

                    return datetime.combine(
                        today,
                        parsed
                    )

                except ValueError:
                    continue

            raise ValueError(
                f"Invalid time format: {value}"
            )

        raise TypeError(
            f"Unsupported time type: {type(value)}"
        )

    # =================================================
    # VALIDATE TIME WINDOW
    # =================================================

    def _validate_window(
        self,
        start_min,
        end_min,
        label
    ):

        if not (
            0 <= start_min < end_min
            <= self.duration_minutes
        ):

            raise ValueError(
                f"Invalid {label} timing. "
                f"Class duration is "
                f"{self.duration_minutes} minutes."
            )

    # =================================================
    # GET CHECK CONFIGURATION
    # =================================================

    def get_check_config(self, check_number):

        configurations = {

            1: (
                "check1_start_min",
                "check1_end_min",
                "check1_camera_minutes"
            ),

            2: (
                "check2_start_min",
                "check2_end_min",
                "check2_camera_minutes"
            ),

            3: (
                "check3_start_min",
                "check3_end_min",
                "check3_camera_minutes"
            )

        }

        if check_number not in configurations:

            raise ValueError(
                "Check number must be 1, 2 or 3."
            )

        start_key, end_key, duration_key = (
            configurations[check_number]
        )

        start_min = int(
            self.settings[start_key]
        )

        end_min = int(
            self.settings[end_key]
        )

        camera_minutes = int(
            self.settings[duration_key]
        )

        self._validate_window(
            start_min,
            end_min,
            f"Check {check_number}"
        )

        if camera_minutes <= 0:

            raise ValueError(
                f"Check {check_number} camera duration "
                "must be greater than zero."
            )

        if camera_minutes > end_min - start_min:

            raise ValueError(
                f"Check {check_number} camera duration "
                "does not fit inside its time window."
            )

        return {

            "window_start": (
                self.class_start
                + timedelta(minutes=start_min)
            ),

            "window_end": (
                self.class_start
                + timedelta(minutes=end_min)
            ),

            "camera_minutes": camera_minutes

        }

    # =================================================
    # VALIDATE COMPLETE ATTENDANCE TIMELINE
    # =================================================

    def _validate_attendance_timeline(self):

        check1 = self.get_check_config(1)
        check2 = self.get_check_config(2)
        check3 = self.get_check_config(3)

        # Check 1 must finish before Check 2 begins
        if check1["window_end"] > check2["window_start"]:

            raise ValueError(
                "Check 1 and Check 2 windows overlap."
            )

        # Check 2 must finish before break begins
        if check2["window_end"] > self.break_start:

            raise ValueError(
                "Check 2 overlaps with the break."
            )

        # Break must finish before Check 3 begins
        if self.break_end > check3["window_start"]:

            raise ValueError(
                "Break overlaps with Check 3."
            )

        # Check 3 must finish within class time
        if check3["window_end"] > self.class_end:

            raise ValueError(
                "Check 3 extends beyond class end time."
            )

        # Check 1 must start after class starts
        if check1["window_start"] < self.class_start:

            raise ValueError(
                "Check 1 cannot start before class begins."
            )

        print("Attendance timing validation successful.")

    # =================================================
    # CAMERA PREPARATION
    # =================================================

    def is_preparing(self):

        now = datetime.now()

        return (
            self.camera_start
            <= now
            < self.class_start
        )

    # =================================================
    # CLASS RUNNING
    # =================================================

    def is_class_running(self):

        now = datetime.now()

        return (
            self.class_start
            <= now
            < self.class_end
        )

    # =================================================
    # BREAK
    # =================================================

    def is_break(self):

        now = datetime.now()

        return (
            self.break_start
            <= now
            < self.break_end
        )

    # =================================================
    # CLASS FINISHED
    # =================================================

    def is_finished(self):

        return datetime.now() >= self.class_end

    # =================================================
    # CAMERA STATUS
    # =================================================

    def camera_should_run(self):

        now = datetime.now()

        if now < self.camera_start:
            return False

        if now >= self.class_end:
            return False

        if self.is_break():
            return False

        return True

    # =================================================
    # CURRENT STATUS
    # =================================================

    def get_status(self):

        now = datetime.now()

        if now < self.camera_start:
            return "WAITING"

        if now < self.class_start:
            return "PREPARING"

        if self.is_break():
            return "BREAK"

        if now < self.class_end:
            return "CLASS_RUNNING"

        return "FINISHED"

    # =================================================
    # BREAK INFORMATION
    # =================================================

    def get_break_info(self):

        return {
            "break_start": self.break_start,
            "break_end": self.break_end
        }
