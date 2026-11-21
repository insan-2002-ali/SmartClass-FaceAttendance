
import os
import cv2
import time
import pickle
import random
import threading

from datetime import datetime, timedelta, time as dt_time

from sklearn.metrics.pairwise import cosine_similarity

from services.camera_service import CameraService
from services.face_detector import FaceDetector
from services.attendance_engine import AttendanceEngine
from services.class_controller import ClassController


class FaceRecognition:

    def __init__(self, stop_event=None):

        self.stop_event = stop_event or threading.Event()

        self.test_mode = (
            os.getenv("ATTENDANCE_TEST_MODE", "0") == "1"
        )

        try:
            self.test_scale = float(
                os.getenv("ATTENDANCE_TEST_SCALE", "1")
            )
        except (TypeError, ValueError):
            self.test_scale = 1.0

        if self.test_scale <= 0:
            self.test_scale = 1.0

        self.embedding_file = (
            "face_data/embeddings/embeddings.pkl"
        )

        self.database = {}
        self.class_database = {}

        self.load_database()

        self.camera = CameraService()
        self.detector = FaceDetector()
        self.engine = AttendanceEngine()

        self.controller = None
        self.schedule = None

        self.class_id = None
        self.teacher_id = None
        self.attendance_id = None

        self.threshold = 0.45

        self.camera_running = False

        self.enrolled_student_numbers = set()
        self.current_check_students = set()

        self.current_check_number = None

        self.runtime_class_start = None
        self.runtime_class_end = None
        self.runtime_break_start = None
        self.runtime_break_end = None

        self.cancelled = False
        self.completed = False

    # =====================================================
    # STOP CONTROL
    # =====================================================

    def is_stopped(self):
        return self.stop_event.is_set()

    def wait_until(self, target_time):

        while datetime.now() < target_time:

            if self.is_stopped():
                return False

            remaining = (
                target_time - datetime.now()
            ).total_seconds()

            if self.stop_event.wait(
                min(1.0, max(0.05, remaining))
            ):
                return False

        return not self.is_stopped()

    # =====================================================
    # LOAD FACE DATABASE
    # =====================================================

    def load_database(self):

        if not os.path.exists(self.embedding_file):

            print("Embedding file not found:")
            print(self.embedding_file)

            self.database = {}
            return

        try:

            with open(self.embedding_file, "rb") as file:
                loaded = pickle.load(file)

            if not isinstance(loaded, dict):
                raise ValueError(
                    "Embedding database must be a dictionary."
                )

            self.database = {
                str(student_id): embedding
                for student_id, embedding in loaded.items()
            }

            print(
                f"Face embeddings loaded: {len(self.database)}"
            )

        except Exception as error:

            print("Could not load embeddings:", error)
            self.database = {}

    # =====================================================
    # MYSQL TIME TO DATETIME
    # =====================================================

    def time_to_datetime(self, value):

        if value is None:
            return None

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
            return datetime.combine(today, value)

        if isinstance(value, str):

            try:
                parsed = datetime.strptime(
                    value,
                    "%H:%M:%S"
                ).time()

            except ValueError:
                parsed = datetime.strptime(
                    value,
                    "%H:%M"
                ).time()

            return datetime.combine(today, parsed)

        raise TypeError(
            f"Unsupported time type: {type(value)}"
        )

    # =====================================================
    # GET ONE SCHEDULE
    # =====================================================

    def get_today_schedule(self):

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

            self.engine.cursor.execute(sql)

            return self.engine.cursor.fetchone()

        today = datetime.now().strftime("%A")

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

        self.engine.cursor.execute(
            sql,
            (today,)
        )

        return self.engine.cursor.fetchone()

    # =====================================================
    # GET ENROLLED STUDENTS
    # =====================================================

    def get_enrolled_students(self):

        sql = """
            SELECT DISTINCT
                s.id,
                s.student_id,
                s.full_name

            FROM classes c

            INNER JOIN teacher_assignments ta
                ON ta.subject_id = c.subject_id
                AND ta.teacher_id = c.teacher_id
                AND ta.department_id = c.department_id
                AND TRIM(ta.semester) = CAST(c.semester AS CHAR)
                AND TRIM(ta.section) = TRIM(c.section)
                AND LEFT(TRIM(ta.academic_year), 4)
                    = CAST(c.academic_year AS CHAR)

            INNER JOIN student_enrollments se
                ON se.teacher_assignment_id = ta.id

            INNER JOIN students s
                ON s.id = se.student_id
                AND s.program_id = c.program_id
                AND s.department_id = c.department_id

            WHERE c.id = %s
              AND c.status = 'Active'
              AND ta.status = 'Active'
              AND se.status = 'Active'
              AND s.status = 'Active'

            ORDER BY s.student_id
        """

        self.engine.cursor.execute(
            sql,
            (self.class_id,)
        )

        return self.engine.cursor.fetchall()

    # =====================================================
    # LOAD CLASS STUDENTS
    # =====================================================

    def load_class_students(self):

        self.class_database = {}
        self.enrolled_student_numbers = set()

        students = self.get_enrolled_students()

        print()
        print("=" * 60)
        print("CLASS STUDENTS")
        print("=" * 60)

        print(f"Enrolled students: {len(students)}")

        for student in students:

            student_number = str(student["student_id"])

            self.enrolled_student_numbers.add(
                student_number
            )

            if student_number in self.database:

                self.class_database[student_number] = (
                    self.database[student_number]
                )

            else:

                print(
                    f"WARNING: No face embedding for "
                    f"{student_number}"
                )

        print(
            f"Face embeddings available: "
            f"{len(self.class_database)}"
        )

        print("=" * 60)

        return len(students) > 0

    # =====================================================
    # RECOGNIZE FACE
    # =====================================================

    def recognize_face(self, embedding):

        best_student = None
        best_score = -1.0

        for student_number, db_embedding in (
            self.class_database.items()
        ):

            if self.is_stopped():
                break

            try:

                score = cosine_similarity(
                    [embedding],
                    [db_embedding]
                )[0][0]

                score = float(score)

            except Exception:
                continue

            if score > best_score:

                best_score = score
                best_student = student_number

        if (
            best_student is not None
            and best_score >= self.threshold
        ):

            return best_student, best_score

        return None, best_score

    # =====================================================
    # CAMERA ON
    # =====================================================

    def start_camera(self):

        if self.is_stopped():
            return False

        if not self.camera_running:

            result = self.camera.start()

            if result is False:
                return False

            self.camera_running = True

            print("Camera ON")

        return True

    # =====================================================
    # CAMERA OFF
    # =====================================================

    def stop_camera(self):

        if self.camera_running:

            try:
                self.camera.stop()

            except Exception as error:
                print("Camera stop warning:", error)

            self.camera_running = False

            print("Camera OFF")

    # =====================================================
    # CREATE ATTENDANCE
    # =====================================================

    def create_attendance(self):

        self.class_id = self.schedule["class_id"]
        self.teacher_id = self.schedule["teacher_id"]

        attendance = self.engine.create_attendance(
            class_id=self.class_id,
            teacher_id=self.teacher_id,
            start_time=self.schedule["start_time"],
            end_time=self.schedule["end_time"]
        )

        if not attendance:

            print("Could not create attendance.")
            return False

        self.attendance_id = attendance["id"]

        print(
            f"Attendance ID: {self.attendance_id}"
        )

        return True

    # =====================================================
    # RANDOM CHECK START
    # =====================================================

    def get_random_check_start(self, config):

        window_start = config["window_start"]
        window_end = config["window_end"]

        camera_duration = config["camera_minutes"]

        latest_start = (
            window_end
            - timedelta(minutes=camera_duration)
        )

        if latest_start < window_start:

            raise ValueError(
                "Camera duration does not fit "
                "inside the check window."
            )

        available_seconds = int(
            (latest_start - window_start).total_seconds()
        )

        random_seconds = random.randint(
            0,
            available_seconds
        )

        return (
            window_start
            + timedelta(seconds=random_seconds)
        )

    # =====================================================
    # CHECK INTERVAL
    # =====================================================

    def get_check_interval(self, check_number):

        config = self.controller.get_check_config(
            check_number
        )

        if check_number == 1:

            camera_start = config["window_start"]

        else:

            camera_start = self.get_random_check_start(
                config
            )

        camera_end = (
            camera_start
            + timedelta(
                minutes=config["camera_minutes"]
            )
        )

        return {
            "start": camera_start,
            "end": camera_end,
            "window_start": config["window_start"],
            "window_end": config["window_end"],
            "camera_minutes": config["camera_minutes"]
        }

    # =====================================================
    # RECORD STUDENT CHECK
    # =====================================================

    def record_student_check(
        self,
        student_number,
        confidence
    ):

        if self.is_stopped():
            return False

        student_number = str(student_number)

        if student_number in self.current_check_students:
            return False

        if student_number not in self.enrolled_student_numbers:
            return False

        student = self.engine.get_student(
            student_number
        )

        if student is None:
            return False

        try:
            confidence = float(confidence)

        except (TypeError, ValueError):
            confidence = None

        result = self.engine.record_check(
            attendance_id=self.attendance_id,
            student_id=student["id"],
            check_number=self.current_check_number,
            status="Present",
            confidence=confidence,
            check_time=datetime.now()
        )

        if result and result.get("success"):

            self.current_check_students.add(
                student_number
            )

            print(
                f"[CHECK {self.current_check_number}] "
                f"{student_number}: PRESENT"
            )

            return True

        if result and result.get("duplicate"):

            self.current_check_students.add(
                student_number
            )

            return False

        print(
            f"Could not record {student_number}: "
            f"{result}"
        )

        return False

    # =====================================================
    # PROCESS FRAME
    # =====================================================

    def process_frame(self, frame):

        if self.is_stopped():
            return frame

        faces = self.detector.detect(frame)

        for face in faces:

            if self.is_stopped():
                break

            embedding = face.embedding

            student_number, score = (
                self.recognize_face(embedding)
            )

            x1, y1, x2, y2 = map(
                int,
                face.bbox
            )

            if student_number is not None:

                student_number = str(student_number)

                color = (0, 255, 0)
                title = student_number

                if (
                    student_number
                    not in self.current_check_students
                ):

                    self.record_student_check(
                        student_number,
                        score
                    )

            else:

                color = (0, 0, 255)
                title = "Unknown Face"

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                color,
                2
            )

            cv2.putText(
                frame,
                title,
                (x1, max(30, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2
            )

            cv2.putText(
                frame,
                f"Confidence: {score:.3f}",
                (x1, y2 + 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color,
                2
            )

        return frame

    # =====================================================
    # RUN ONE CHECK
    # =====================================================

    def run_check(
        self,
        check_number,
        check_start,
        check_end,
        check_name
    ):

        if self.is_stopped():
            return False

        self.current_check_number = check_number
        self.current_check_students = set()

        now = datetime.now()

        if now >= check_end:

            print(
                f"CHECK {check_number} SKIPPED: "
                "Its time window has ended."
            )

            return True

        if now < check_start:

            self.stop_camera()

            if not self.wait_until(check_start):
                return False

        actual_start = max(
            datetime.now(),
            check_start
        )

        if actual_start >= check_end:
            return True

        print()
        print("=" * 60)
        print(f"CHECK {check_number}: {check_name}")

        print(
            "Start:",
            actual_start.strftime("%H:%M:%S")
        )

        print(
            "End:",
            check_end.strftime("%H:%M:%S")
        )

        print("=" * 60)

        if not self.start_camera():
            return False

        try:

            while (
                datetime.now() < check_end
                and not self.is_stopped()
            ):

                success, frame = self.camera.read()

                if not success:

                    if self.stop_event.wait(0.05):
                        break

                    continue

                frame = self.process_frame(frame)

                remaining = max(
                    0,
                    int(
                        (
                            check_end - datetime.now()
                        ).total_seconds()
                    )
                )

                cv2.putText(
                    frame,
                    f"CHECK {check_number} | {remaining}s",
                    (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 255),
                    2
                )

                cv2.putText(
                    frame,
                    (
                        "Recognized: "
                        f"{len(self.current_check_students)}"
                    ),
                    (20, 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    frame,
                    "Attendance requires 2 of 3 checks",
                    (20, 105),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 0),
                    2
                )

                cv2.imshow(
                    "AI Attendance System",
                    frame
                )

                key = cv2.waitKey(1) & 0xFF

                if key == 27:

                    print("ESC pressed.")
                    self.cancelled = True
                    return False

        finally:

            self.stop_camera()

        if self.is_stopped():
            return False

        print()
        print(
            f"CHECK {check_number} COMPLETED"
        )

        print(
            "Recognized students:",
            len(self.current_check_students)
        )

        return True

    # =====================================================
    # BREAK
    # =====================================================

    def run_break(
        self,
        break_start,
        break_end
    ):

        print()
        print("=" * 60)
        print("CLASS BREAK")
        print(
            break_start.strftime("%H:%M:%S"),
            "→",
            break_end.strftime("%H:%M:%S")
        )
        print("Camera OFF")
        print("=" * 60)

        self.stop_camera()

        if datetime.now() < break_start:

            if not self.wait_until(break_start):
                return False

        if datetime.now() < break_end:

            if not self.wait_until(break_end):
                return False

        return not self.is_stopped()

    # =====================================================
    # CANCEL OPEN ATTENDANCE
    # =====================================================

    def cancel_open_attendance(self):

        if not self.attendance_id or self.completed:
            return False

        try:

            cancelled = self.engine.cancel_attendance(
                self.attendance_id
            )

            if cancelled:

                self.cancelled = True

                print(
                    f"Attendance {self.attendance_id} cancelled."
                )

            return cancelled

        except Exception as error:

            print(
                "Attendance cancellation error:",
                error
            )

            return False

    # =====================================================
    # FINALIZE ATTENDANCE
    # =====================================================

    def finalize_class(self):

        if self.is_stopped():
            print("Finalization skipped: stop requested.")
            return False

        print()
        print("=" * 60)
        print("FINALIZING ATTENDANCE")
        print("=" * 60)

        students = self.get_enrolled_students()

        student_ids = [
            student["id"]
            for student in students
        ]

        summary = self.engine.finalize_check_attendance(
            attendance_id=self.attendance_id,
            student_ids=student_ids
        )

        if not summary:
            print("Attendance finalization failed.")
            return False

        print()
        print("=" * 60)
        print("ATTENDANCE SUMMARY")
        print("=" * 60)

        print(
            "Total Students:",
            summary["total_students"]
        )

        print(
            "Present:",
            summary["present_students"]
        )

        print(
            "Absent:",
            summary["absent_students"]
        )

        print("=" * 60)

        self.completed = True

        return True

    # =====================================================
    # PREPARATION CAMERA
    # =====================================================

    def preparation_camera(
        self,
        preparation_start,
        class_start
    ):

        if self.is_stopped():
            return False

        print()
        print("=" * 60)
        print("CLASS PREPARATION")
        print("Camera ON")
        print("Attendance recording OFF")
        print("=" * 60)

        if not self.start_camera():
            return False

        try:

            while (
                datetime.now() < class_start
                and not self.is_stopped()
            ):

                success, frame = self.camera.read()

                if not success:

                    if self.stop_event.wait(0.05):
                        break

                    continue

                seconds = max(
                    0,
                    int(
                        (
                            class_start - datetime.now()
                        ).total_seconds()
                    )
                )

                cv2.putText(
                    frame,
                    "CLASS STARTING SOON",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (0, 255, 255),
                    2
                )

                cv2.putText(
                    frame,
                    f"Starting in {seconds}s",
                    (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2
                )

                cv2.imshow(
                    "AI Attendance System",
                    frame
                )

                key = cv2.waitKey(1) & 0xFF

                if key == 27:

                    print("ESC pressed.")
                    self.cancelled = True
                    return False

        finally:

            self.stop_camera()

        return not self.is_stopped()

    # =====================================================
    # PRODUCTION SCHEDULE
    # =====================================================

    def run_production_schedule(self):

        class_start = self.controller.class_start
        class_end = self.controller.class_end

        break_start = self.controller.break_start
        break_end = self.controller.break_end

        self.runtime_class_start = class_start
        self.runtime_class_end = class_end
        self.runtime_break_start = break_start
        self.runtime_break_end = break_end

        check_1 = self.get_check_interval(1)
        check_2 = self.get_check_interval(2)
        check_3 = self.get_check_interval(3)

        print()
        print("=" * 60)
        print("THREE-CHECK ATTENDANCE")
        print("=" * 60)

        for number, config in (
            (1, check_1),
            (2, check_2),
            (3, check_3)
        ):

            print(
                f"CHECK {number}: "
                f"{config['start'].strftime('%H:%M:%S')} "
                f"→ {config['end'].strftime('%H:%M:%S')}"
            )

        print(
            "BREAK:",
            break_start.strftime("%H:%M:%S"),
            "→",
            break_end.strftime("%H:%M:%S")
        )

        print("Minimum required: 2 / 3")
        print("=" * 60)

        preparation_start = self.controller.camera_start

        if datetime.now() < preparation_start:

            if not self.wait_until(preparation_start):
                return False

        if self.is_stopped():
            return False

        if datetime.now() < class_start:

            if not self.preparation_camera(
                preparation_start,
                class_start
            ):
                return False

        if not self.run_check(
            1,
            check_1["start"],
            check_1["end"],
            "FIXED FIRST CHECK"
        ):
            return False

        if not self.run_check(
            2,
            check_2["start"],
            check_2["end"],
            "RANDOM SECOND CHECK"
        ):
            return False

        if not self.run_break(
            break_start,
            break_end
        ):
            return False

        if not self.run_check(
            3,
            check_3["start"],
            check_3["end"],
            "RANDOM THIRD CHECK"
        ):
            return False

        self.stop_camera()

        if datetime.now() < class_end:

            print("All checks completed.")
            print("Waiting until class end...")

            if not self.wait_until(class_end):
                return False

        if self.is_stopped():
            return False

        return self.finalize_class()

    # =====================================================
    # TEST SCHEDULE
    # =====================================================

    def run_test_schedule(self):

        scale = self.test_scale

        now = datetime.now().replace(
            microsecond=0
        )

        check_1_start = now

        check_1_end = (
            check_1_start
            + timedelta(seconds=10 * scale)
        )

        check_2_start = (
            check_1_end
            + timedelta(seconds=5 * scale)
        )

        check_2_end = (
            check_2_start
            + timedelta(seconds=5 * scale)
        )

        break_start = check_2_end

        break_end = (
            break_start
            + timedelta(seconds=10 * scale)
        )

        check_3_start = break_end

        check_3_end = (
            check_3_start
            + timedelta(seconds=5 * scale)
        )

        print()
        print("=" * 60)
        print("TEST MODE")
        print("=" * 60)

        if not self.run_check(
            1,
            check_1_start,
            check_1_end,
            "TEST CHECK 1"
        ):
            return False

        if not self.run_check(
            2,
            check_2_start,
            check_2_end,
            "TEST CHECK 2"
        ):
            return False

        if not self.run_break(
            break_start,
            break_end
        ):
            return False

        if not self.run_check(
            3,
            check_3_start,
            check_3_end,
            "TEST CHECK 3"
        ):
            return False

        if self.is_stopped():
            return False

        return self.finalize_class()

    # =====================================================
    # START ONE CLASS WORKER
    # =====================================================

    def start(self, schedule=None):

        if self.is_stopped():
            return False

        self.schedule = (
            schedule or self.get_today_schedule()
        )

        if self.schedule is None:

            print("No class schedule found.")
            return False

        self.controller = ClassController(
            self.schedule
        )

        print()
        print("=" * 60)
        print("CLASS ATTENDANCE WORKER")
        print("=" * 60)

        print(
            "Class:",
            self.schedule["class_name"]
        )

        print(
            "Class ID:",
            self.schedule["class_id"]
        )

        print(
            "Start:",
            self.schedule["start_time"]
        )

        print(
            "End:",
            self.schedule["end_time"]
        )

        print(
            "Break:",
            self.controller.break_start.strftime("%H:%M:%S"),
            "→",
            self.controller.break_end.strftime("%H:%M:%S")
        )

        print("=" * 60)

        if not self.test_mode:

            if datetime.now() >= self.controller.class_end:

                print("Class already finished.")
                return False

            if datetime.now() < self.controller.camera_start:

                print("Waiting for preparation time...")

                if not self.wait_until(
                    self.controller.camera_start
                ):
                    return False

        if self.is_stopped():
            return False

        if not self.create_attendance():
            return False

        if self.is_stopped():
            return False

        if not self.load_class_students():

            print("No enrolled students found.")
            return False

        if self.is_stopped():
            return False

        if self.test_mode:
            return self.run_test_schedule()

        return self.run_production_schedule()

    # =====================================================
    # CLOSE
    # =====================================================

    def close(self):

        self.stop_camera()

        # Cancel attendance if it was not finalized.
        if not self.completed:
            self.cancel_open_attendance()

        try:
            self.engine.close()

        except Exception as error:
            print("Engine close warning:", error)

        try:
            cv2.destroyAllWindows()

        except Exception:
            pass


# =========================================================
# STANDALONE TEST
# =========================================================

def main():

    print("=" * 60)
    print("AI ATTENDANCE SYSTEM")
    print("=" * 60)

    recognition = FaceRecognition()

    try:

        if not recognition.database:

            print("No face embeddings found.")
            print(
                "Run: python -m services.face_encoder"
            )

            return

        print(
            f"Loaded {len(recognition.database)} "
            "face embeddings."
        )

        recognition.start()

    except KeyboardInterrupt:

        print("Stopped by user.")
        recognition.stop_event.set()

    except Exception as error:

        print("Attendance error:", error)

    finally:

        recognition.close()


if __name__ == "__main__":
    main()
