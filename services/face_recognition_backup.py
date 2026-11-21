import os
import cv2
import time
import pickle

from datetime import datetime, timedelta

from sklearn.metrics.pairwise import cosine_similarity

from services.camera_service import CameraService
from services.face_detector import FaceDetector
from services.attendance_engine import AttendanceEngine
from services.class_controller import ClassController


class FaceRecognition:

    # =====================================================
    # INITIALIZATION
    # =====================================================

    def __init__(self):

        # -------------------------------------------------
        # TEST MODE
        #
        # ATTENDANCE_TEST_MODE=1
        # ATTENDANCE_TEST_SCALE=1
        # python -m services.face_recognition
        # -------------------------------------------------

        self.test_mode = (
            os.getenv(
                "ATTENDANCE_TEST_MODE",
                "0"
            ) == "1"
        )

        try:

            self.test_scale = float(
                os.getenv(
                    "ATTENDANCE_TEST_SCALE",
                    "1"
                )
            )

        except ValueError:

            self.test_scale = 1

        if self.test_scale <= 0:

            self.test_scale = 1

        # =================================================
        # FACE DATABASE
        # =================================================

        self.embedding_file = (
            "face_data/embeddings/embeddings.pkl"
        )

        self.database = {}

        self.class_database = {}

        self.load_database()

        # =================================================
        # SERVICES
        # =================================================

        self.camera = CameraService()

        self.detector = FaceDetector()

        self.engine = AttendanceEngine()

        # =================================================
        # CLASS
        # =================================================

        self.controller = None

        self.schedule = None

        self.class_id = None

        self.teacher_id = None

        self.attendance_id = None

        # =================================================
        # FACE MATCH
        # =================================================

        self.threshold = 0.45

        # =================================================
        # CAMERA
        # =================================================

        self.camera_running = False

        # =================================================
        # STUDENTS
        # =================================================

        self.enrolled_student_numbers = set()

        # Students detected during current check.
        self.current_check_students = set()

        # =================================================
        # RUNTIME
        # =================================================

        self.runtime_class_start = None

        self.runtime_class_end = None

        self.runtime_break_start = None

        self.runtime_break_end = None

        # =================================================
        # CURRENT CHECK NUMBER
        # =================================================

        self.current_check_number = None

    # =====================================================
    # LOAD FACE DATABASE
    # =====================================================

    def load_database(self):

        if not os.path.exists(
            self.embedding_file
        ):

            print(
                "Embedding file not found:"
            )

            print(
                self.embedding_file
            )

            self.database = {}

            return

        try:

            with open(
                self.embedding_file,
                "rb"
            ) as file:

                self.database = pickle.load(
                    file
                )

            self.database = {
                str(student_id): embedding
                for student_id, embedding
                in self.database.items()
            }

        except Exception as error:

            print(
                f"Could not load embeddings: "
                f"{error}"
            )

            self.database = {}

    # =====================================================
    # GET TODAY'S CLASS
    # =====================================================

    def get_today_schedule(self):

        today = datetime.now().strftime(
            "%A"
        )

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

        ORDER BY cs.start_time

        LIMIT 1
        """

        self.engine.cursor.execute(
            sql,
            (today,)
        )

        return self.engine.cursor.fetchone()

    # =====================================================
    # LOAD ONLY ENROLLED STUDENTS
    # =====================================================

    def load_class_students(self):

        self.class_database = {}

        self.enrolled_student_numbers = set()

        sql = """
        SELECT DISTINCT
            s.id,
            s.student_id

        FROM students s

        INNER JOIN student_enrollments se
            ON se.student_id = s.id

        INNER JOIN teacher_assignments ta
            ON ta.id = se.teacher_assignment_id

        INNER JOIN classes c
            ON c.subject_id = ta.subject_id

            AND c.teacher_id = ta.teacher_id

            AND c.department_id = ta.department_id

        WHERE c.id = %s

        AND c.status = 'Active'

        AND ta.status = 'Active'

        AND se.status = 'Active'
        """

        self.engine.cursor.execute(
            sql,
            (self.class_id,)
        )

        students = (
            self.engine.cursor.fetchall()
        )

        print()
        print("=" * 60)
        print("CLASS STUDENTS")
        print("=" * 60)

        print(
            f"Enrolled students : "
            f"{len(students)}"
        )

        for student in students:

            student_number = str(
                student["student_id"]
            )

            self.enrolled_student_numbers.add(
                student_number
            )

            if (
                student_number
                in self.database
            ):

                self.class_database[
                    student_number
                ] = self.database[
                    student_number
                ]

            else:

                print(
                    f"WARNING: No face embedding "
                    f"for {student_number}"
                )

        print(
            f"Face embeddings loaded : "
            f"{len(self.class_database)}"
        )

        print("=" * 60)

        return len(students) > 0

    # =====================================================
    # RECOGNIZE FACE
    # =====================================================

    def recognize_face(
        self,
        embedding
    ):

        best_student = None

        best_score = -1.0

        for (
            student_number,
            db_embedding
        ) in self.class_database.items():

            try:

                score = cosine_similarity(
                    [embedding],
                    [db_embedding]
                )[0][0]

            except Exception:

                continue

            if score > best_score:

                best_score = score

                best_student = (
                    student_number
                )

        if (
            best_student is not None
            and best_score >= self.threshold
        ):

            return (
                best_student,
                best_score
            )

        return (
            None,
            best_score
        )

    # =====================================================
    # CAMERA ON
    # =====================================================

    def start_camera(self):

        if not self.camera_running:

            self.camera.start()

            self.camera_running = True

            print(
                "Camera ON"
            )

    # =====================================================
    # CAMERA OFF
    # =====================================================

    def stop_camera(self):

        if self.camera_running:

            try:

                self.camera.stop()

            except Exception:

                pass

            self.camera_running = False

            print(
                "Camera OFF"
            )

    # =====================================================
    # CREATE ATTENDANCE
    # =====================================================

    def create_attendance(self):

        self.class_id = (
            self.schedule["class_id"]
        )

        self.teacher_id = (
            self.schedule["teacher_id"]
        )

        attendance = (
            self.engine.create_attendance(
                class_id=self.class_id,
                teacher_id=self.teacher_id,
                start_time=self.schedule[
                    "start_time"
                ],
                end_time=self.schedule[
                    "end_time"
                ]
            )
        )

        if attendance:

            self.attendance_id = (
                attendance["id"]
            )

            print()
            print(
                f"Attendance ID : "
                f"{self.attendance_id}"
            )

            return True

        print(
            "Could not create attendance."
        )

        return False

    # =====================================================
    # WAIT
    # =====================================================

    def wait_until(
        self,
        target_time
    ):

        while (
            datetime.now()
            < target_time
        ):

            remaining = (
                target_time
                - datetime.now()
            ).total_seconds()

            time.sleep(
                min(
                    1.0,
                    max(
                        0.05,
                        remaining
                    )
                )
            )

    # =====================================================
    # RECORD ONE CHECK RESULT
    #
    # IMPORTANT:
    #
    # One student can be counted only ONCE
    # during one check.
    #
    # The database UNIQUE KEY protects this too.
    # =====================================================

    def record_student_check(
        self,
        student_number,
        confidence
    ):

        student = (
            self.engine.get_student(
                student_number
            )
        )

        if student is None:

            return False

        student_id = student["id"]

        result = (
            self.engine.record_check(
                attendance_id=self.attendance_id,
                student_id=student_id,
                check_number=self.current_check_number,
                status="Present",
                confidence=confidence,
                check_time=datetime.now()
            )
        )

        if result["success"]:

            print(
                f"[CHECK "
                f"{self.current_check_number}] "
                f"{student_number} -> Present"
            )

            return True

        if result.get("duplicate"):

            return False

        print(
            f"Check recording failed for "
            f"{student_number}: "
            f"{result.get('message')}"
        )

        return False

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

        self.current_check_number = (
            check_number
        )

        self.current_check_students = set()

        print()
        print("=" * 60)

        print(
            f"CHECK {check_number} : "
            f"{check_name}"
        )

        print(
            "Start :",
            check_start.strftime(
                "%H:%M:%S"
            )
        )

        print(
            "End   :",
            check_end.strftime(
                "%H:%M:%S"
            )
        )

        print("=" * 60)

        # =================================================
        # CAMERA ON
        # =================================================

        self.start_camera()

        # =================================================
        # CAMERA LOOP
        # =================================================

        while (
            datetime.now()
            < check_end
        ):

            success, frame = (
                self.camera.read()
            )

            if not success:

                print(
                    "Camera read failed."
                )

                time.sleep(
                    0.05
                )

                continue

            # =================================================
            # DETECT ALL FACES
            # =================================================

            faces = (
                self.detector.detect(
                    frame
                )
            )

            # =================================================
            # PROCESS EVERY FACE
            # =================================================

            for face in faces:

                embedding = (
                    face.embedding
                )

                (
                    student_number,
                    score
                ) = self.recognize_face(
                    embedding
                )

                x1, y1, x2, y2 = map(
                    int,
                    face.bbox
                )

                # =================================================
                # KNOWN STUDENT
                # =================================================

                if student_number is not None:

                    student_number = str(
                        student_number
                    )

                    color = (
                        0,
                        255,
                        0
                    )

                    # ---------------------------------------------
                    # FIRST TIME DURING THIS CHECK
                    # ---------------------------------------------

                    if (
                        student_number
                        not in
                        self.current_check_students
                    ):

                        self.current_check_students.add(
                            student_number
                        )

                        self.record_student_check(
                            student_number=student_number,
                            confidence=score
                        )

                    label = (
                        f"{student_number} "
                        f"{score * 100:.1f}% "
                        f"CHECK "
                        f"{check_number}"
                    )

                # =================================================
                # UNKNOWN
                # =================================================

                else:

                    color = (
                        0,
                        0,
                        255
                    )

                    label = (
                        "Unknown "
                        f"{max(score, 0) * 100:.1f}%"
                    )

                # =================================================
                # DRAW BOX
                # =================================================

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    color,
                    2
                )

                cv2.putText(
                    frame,
                    label,
                    (
                        x1,
                        max(
                            25,
                            y1 - 10
                        )
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    color,
                    2
                )

            # =================================================
            # SCREEN STATUS
            # =================================================

            remaining = (
                check_end
                - datetime.now()
            ).total_seconds()

            seconds = max(
                0,
                int(remaining)
            )

            cv2.putText(
                frame,
                f"CHECK {check_number} "
                f"- {seconds}s",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"Detected: "
                f"{len(self.current_check_students)}",
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                "ESC = Exit",
                (20, 105),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            cv2.imshow(
                "AI Attendance System",
                frame
            )

            key = (
                cv2.waitKey(1)
                & 0xFF
            )

            if key == 27:

                print()
                print(
                    "ESC pressed."
                )

                self.stop_camera()

                return False

            time.sleep(
                0.001
            )

        # =================================================
        # CHECK RESULT
        # =================================================

        print()
        print(
            "CHECK RESULT"
        )

        print(
            "-" * 60
        )

        if self.current_check_students:

            for student_number in sorted(
                self.current_check_students
            ):

                print(
                    f"{student_number} "
                    f"-> Present"
                )

        else:

            print(
                "No recognized student "
                "during this check."
            )

        # =================================================
        # CAMERA OFF
        # =================================================

        self.stop_camera()

        self.current_check_students = set()

        return True

    # =====================================================
    # PRINT BREAK
    # =====================================================

    def run_break(
        self,
        break_start,
        break_end
    ):

        if (
            datetime.now()
            < break_start
        ):

            self.wait_until(
                break_start
            )

        print()
        print("=" * 60)

        print(
            "BREAK"
        )

        print(
            f"{break_start.strftime('%H:%M:%S')}"
            " → "
            f"{break_end.strftime('%H:%M:%S')}"
        )

        print(
            "Camera OFF"
        )

        print(
            "No Face Check"
        )

        print("=" * 60)

        self.stop_camera()

        if (
            datetime.now()
            < break_end
        ):

            self.wait_until(
                break_end
            )

    # =====================================================
    # FINALIZE CLASS
    #
    # 4 checks:
    #
    # 4/4 = Present
    # 3/4 = Present
    # 2/4 = Partial
    # 1/4 = Absent
    # 0/4 = Absent
    # =====================================================

    def finalize_class(
        self,
        class_start,
        class_end,
        break_start,
        break_end
    ):

        print()
        print("=" * 60)
        print(
            "FINALIZING ATTENDANCE"
        )
        print("=" * 60)

        # =================================================
        # GET ENROLLED STUDENTS
        # =================================================

        sql = """
        SELECT DISTINCT
            s.id,
            s.student_id

        FROM students s

        INNER JOIN student_enrollments se
            ON se.student_id = s.id

        INNER JOIN teacher_assignments ta
            ON ta.id = se.teacher_assignment_id

        INNER JOIN classes c
            ON c.subject_id = ta.subject_id

            AND c.teacher_id = ta.teacher_id

            AND c.department_id = ta.department_id

        WHERE c.id = %s

        AND c.status = 'Active'

        AND ta.status = 'Active'

        AND se.status = 'Active'
        """

        self.engine.cursor.execute(
            sql,
            (self.class_id,)
        )

        students = (
            self.engine.cursor.fetchall()
        )

        print(
            f"Total Students : "
            f"{len(students)}"
        )

        # =================================================
        # PROCESS EACH STUDENT
        # =================================================

        present_students = 0

        partial_students = 0

        absent_students = 0

        for student in students:

            student_id = (
                student["id"]
            )

            student_number = str(
                student["student_id"]
            )

            # ---------------------------------------------
            # Make sure session exists
            # ---------------------------------------------

            self.engine.get_or_create_session(
                attendance_id=self.attendance_id,
                student_id=student_id
            )

            # ---------------------------------------------
            # Get 4-check result
            # ---------------------------------------------

            result = (
                self.engine.calculate_check_status(
                    attendance_id=self.attendance_id,
                    student_id=student_id,
                    total_checks=4
                )
            )

            checks = result["checks"]

            percentage = result[
                "percentage"
            ]

            status = result[
                "status"
            ]

            # ---------------------------------------------
            # Update session
            # ---------------------------------------------

            self.engine.cursor.execute(
                """
                UPDATE attendance_sessions

                SET
                    total_present_seconds = %s,
                    total_absent_seconds = %s,
                    attendance_percentage = %s,
                    status = %s

                WHERE attendance_id = %s

                AND student_id = %s
                """,
                (
                    0,
                    0,
                    percentage,
                    status,
                    self.attendance_id,
                    student_id
                )
            )

            # ---------------------------------------------
            # Save attendance_details only once
            # for final status
            # ---------------------------------------------

            self.engine.cursor.execute(
                """
                SELECT id

                FROM attendance_details

                WHERE attendance_id = %s

                AND student_id = %s

                LIMIT 1
                """,
                (
                    self.attendance_id,
                    student_id
                )
            )

            detail_exists = (
                self.engine.cursor.fetchone()
            )

            if not detail_exists:

                # Get best confidence
                self.engine.cursor.execute(
                    """
                    SELECT
                        MAX(confidence_score)
                        AS confidence

                    FROM attendance_check_results

                    WHERE attendance_id = %s

                    AND student_id = %s

                    AND status = 'Present'
                    """,
                    (
                        self.attendance_id,
                        student_id
                    )
                )

                confidence_result = (
                    self.engine.cursor.fetchone()
                )

                confidence = None

                if confidence_result:

                    confidence = (
                        confidence_result[
                            "confidence"
                        ]
                    )

                self.engine.cursor.execute(
                    """
                    INSERT INTO attendance_details
                    (
                        attendance_id,
                        student_id,
                        attendance_time,
                        attendance_status,
                        confidence_score,
                        remarks
                    )

                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        self.attendance_id,
                        student_id,
                        datetime.now(),
                        status,
                        confidence,
                        (
                            f"{checks}/4 checks"
                        )
                    )
                )

            # ---------------------------------------------
            # Count summary
            # ---------------------------------------------

            if status == "Present":

                present_students += 1

            elif status == "Partial":

                partial_students += 1

            else:

                absent_students += 1

            print(
                f"{student_number} "
                f"-> {status} "
                f"({checks}/4, "
                f"{percentage:.2f}%)"
            )

        # =================================================
        # UPDATE ATTENDANCE SUMMARY
        #
        # Important:
        #
        # attendance.present_students =
        # fully Present students
        #
        # attendance.absent_students =
        # Partial + Absent students
        # =================================================

        self.engine.cursor.execute(
            """
            UPDATE attendance

            SET
                total_students = %s,

                present_students = %s,

                absent_students = %s,

                status = 'Completed',

                end_time = %s

            WHERE id = %s
            """,
            (
                len(students),
                present_students,
                (
                    partial_students
                    +
                    absent_students
                ),
                datetime.now().time(),
                self.attendance_id
            )
        )

        self.engine.connection.commit()

        print()
        print(
            "Present :",
            present_students
        )

        print(
            "Partial :",
            partial_students
        )

        print(
            "Absent  :",
            absent_students
        )

        print()
        print("=" * 60)
        print(
            "ATTENDANCE COMPLETED"
        )
        print("=" * 60)

    # =====================================================
    # PRODUCTION SCHEDULE
    #
    # EXACTLY 4 CHECKS
    #
    # 1. First 10 minutes
    # 2. Last 5 minutes before break
    # 3. First 5 minutes after break
    # 4. Last 7 minutes before class end
    # =====================================================

    def run_production_schedule(self):

        class_start = (
            self.controller.class_start
        )

        class_end = (
            self.controller.class_end
        )

        break_start = (
            self.controller.break_start
        )

        break_end = (
            self.controller.break_end
        )

        self.runtime_class_start = (
            class_start
        )

        self.runtime_class_end = (
            class_end
        )

        self.runtime_break_start = (
            break_start
        )

        self.runtime_break_end = (
            break_end
        )

        # =================================================
        # CHECK 1
        # First 10 minutes
        # =================================================

        check_1_start = (
            class_start
        )

        check_1_end = min(
            class_start
            + timedelta(
                minutes=10
            ),
            break_start
        )

        if (
            datetime.now()
            < check_1_start
        ):

            self.wait_until(
                check_1_start
            )

        if (
            datetime.now()
            < check_1_end
        ):

            if not self.run_check(
                1,
                check_1_start,
                check_1_end,
                "FIRST 10 MINUTES"
            ):

                return False

        # =================================================
        # CHECK 2
        # Last 5 minutes before break
        # =================================================

        check_2_start = max(
            class_start,
            break_start
            - timedelta(
                minutes=5
            )
        )

        check_2_end = break_start

        if (
            datetime.now()
            < check_2_start
        ):

            self.wait_until(
                check_2_start
            )

        if (
            datetime.now()
            < check_2_end
        ):

            if not self.run_check(
                2,
                check_2_start,
                check_2_end,
                "BEFORE BREAK"
            ):

                return False

        # =================================================
        # BREAK
        # =================================================

        self.run_break(
            break_start,
            break_end
        )

        # =================================================
        # CHECK 3
        # First 5 minutes after break
        # =================================================

        check_3_start = (
            break_end
        )

        check_3_end = min(
            break_end
            + timedelta(
                minutes=5
            ),
            class_end
        )

        if (
            datetime.now()
            < check_3_start
        ):

            self.wait_until(
                check_3_start
            )

        if (
            datetime.now()
            < check_3_end
        ):

            if not self.run_check(
                3,
                check_3_start,
                check_3_end,
                "AFTER BREAK"
            ):

                return False

        # =================================================
        # CHECK 4
        # Last 7 minutes before class end
        # =================================================

        check_4_start = max(
            break_end,
            class_end
            - timedelta(
                minutes=7
            )
        )

        check_4_end = (
            class_end
        )

        if (
            datetime.now()
            < check_4_start
        ):

            self.wait_until(
                check_4_start
            )

        if (
            datetime.now()
            < check_4_end
        ):

            if not self.run_check(
                4,
                check_4_start,
                check_4_end,
                "FINAL 7 MINUTES"
            ):

                return False

        # =================================================
        # FINALIZE
        # =================================================

        self.stop_camera()

        self.finalize_class(
            class_start,
            class_end,
            break_start,
            break_end
        )

        return True

    # =====================================================
    # TEST SCHEDULE
    #
    # EXACTLY 4 CHECKS
    #
    # Test mode is short so you don't have to wait
    # for a real class.
    # =====================================================

    def run_test_schedule(self):

        scale = self.test_scale

        now = (
            datetime.now()
            .replace(
                microsecond=0
            )
        )

        # =================================================
        # TEST CHECK 1
        # 10 seconds
        # =================================================

        check_1_start = now

        check_1_end = (
            check_1_start
            + timedelta(
                seconds=10 * scale
            )
        )

        # =================================================
        # GAP BEFORE CHECK 2
        # =================================================

        check_2_start = (
            check_1_end
            + timedelta(
                seconds=5 * scale
            )
        )

        # =================================================
        # TEST CHECK 2
        # 5 seconds
        # =================================================

        check_2_end = (
            check_2_start
            + timedelta(
                seconds=5 * scale
            )
        )

        # =================================================
        # TEST BREAK
        # 10 seconds
        # =================================================

        break_start = (
            check_2_end
        )

        break_end = (
            break_start
            + timedelta(
                seconds=10 * scale
            )
        )

        # =================================================
        # TEST CHECK 3
        # 5 seconds
        # =================================================

        check_3_start = (
            break_end
        )

        check_3_end = (
            check_3_start
            + timedelta(
                seconds=5 * scale
            )
        )

        # =================================================
        # GAP BEFORE FINAL CHECK
        # =================================================

        check_4_start = (
            check_3_end
            + timedelta(
                seconds=5 * scale
            )
        )

        # =================================================
        # TEST CHECK 4
        # 7 seconds
        # =================================================

        check_4_end = (
            check_4_start
            + timedelta(
                seconds=7 * scale
            )
        )

        class_start = (
            check_1_start
        )

        class_end = (
            check_4_end
        )

        self.runtime_class_start = (
            class_start
        )

        self.runtime_class_end = (
            class_end
        )

        self.runtime_break_start = (
            break_start
        )

        self.runtime_break_end = (
            break_end
        )

        print()
        print("=" * 60)
        print(
            "TEST MODE ENABLED"
        )
        print("=" * 60)

        print(
            "CHECK 1 :",
            check_1_start.strftime(
                "%H:%M:%S"
            ),
            "→",
            check_1_end.strftime(
                "%H:%M:%S"
            )
        )

        print(
            "CHECK 2 :",
            check_2_start.strftime(
                "%H:%M:%S"
            ),
            "→",
            check_2_end.strftime(
                "%H:%M:%S"
            )
        )

        print(
            "BREAK   :",
            break_start.strftime(
                "%H:%M:%S"
            ),
            "→",
            break_end.strftime(
                "%H:%M:%S"
            )
        )

        print(
            "CHECK 3 :",
            check_3_start.strftime(
                "%H:%M:%S"
            ),
            "→",
            check_3_end.strftime(
                "%H:%M:%S"
            )
        )

        print(
            "CHECK 4 :",
            check_4_start.strftime(
                "%H:%M:%S"
            ),
            "→",
            check_4_end.strftime(
                "%H:%M:%S"
            )
        )

        print("=" * 60)

        # =================================================
        # CHECK 1
        # =================================================

        if not self.run_check(
            1,
            check_1_start,
            check_1_end,
            "TEST CHECK 1"
        ):

            return False

        # =================================================
        # WAIT CHECK 2
        # =================================================

        self.wait_until(
            check_2_start
        )

        # =================================================
        # CHECK 2
        # =================================================

        if not self.run_check(
            2,
            check_2_start,
            check_2_end,
            "TEST CHECK 2"
        ):

            return False

        # =================================================
        # BREAK
        # =================================================

        self.run_break(
            break_start,
            break_end
        )

        # =================================================
        # CHECK 3
        # =================================================

        if not self.run_check(
            3,
            check_3_start,
            check_3_end,
            "TEST CHECK 3"
        ):

            return False

        # =================================================
        # WAIT CHECK 4
        # =================================================

        self.wait_until(
            check_4_start
        )

        # =================================================
        # CHECK 4
        # =================================================

        if not self.run_check(
            4,
            check_4_start,
            check_4_end,
            "TEST CHECK 4"
        ):

            return False

        # =================================================
        # FINALIZE
        # =================================================

        self.stop_camera()

        self.finalize_class(
            class_start,
            class_end,
            break_start,
            break_end
        )

        return True

    # =====================================================
    # START
    # =====================================================

    def start(self):

        # =================================================
        # GET TODAY'S CLASS
        # =================================================

        self.schedule = (
            self.get_today_schedule()
        )

        if self.schedule is None:

            print()
            print(
                "No class scheduled for today."
            )

            return

        # =================================================
        # CLASS CONTROLLER
        # =================================================

        self.controller = (
            ClassController(
                self.schedule
            )
        )

        # =================================================
        # CLASS INFORMATION
        # =================================================

        print()
        print("=" * 60)

        print(
            "TODAY'S CLASS"
        )

        print("=" * 60)

        print(
            "Day :",
            self.schedule[
                "day_of_week"
            ]
        )

        print(
            "Class :",
            self.schedule[
                "class_name"
            ]
        )

        print(
            "Start :",
            self.schedule[
                "start_time"
            ]
        )

        print(
            "Break Start :",
            self.controller.break_start.strftime(
                "%H:%M:%S"
            )
        )

        print(
            "Break End :",
            self.controller.break_end.strftime(
                "%H:%M:%S"
            )
        )

        print(
            "End :",
            self.schedule[
                "end_time"
            ]
        )

        print("=" * 60)

        # =================================================
        # CREATE ATTENDANCE
        # =================================================

        if not self.create_attendance():

            return

        # =================================================
        # LOAD STUDENTS
        # =================================================

        if not self.load_class_students():

            print()
            print(
                "No enrolled students found."
            )

            return

        # =================================================
        # TEST MODE
        # =================================================

        if self.test_mode:

            self.run_test_schedule()

            return

        # =================================================
        # PRODUCTION
        # =================================================

        self.run_production_schedule()

    # =====================================================
    # CLOSE
    # =====================================================

    def close(self):

        self.stop_camera()

        try:

            self.engine.close()

        except Exception:

            pass

        cv2.destroyAllWindows()


# =========================================================
# MAIN
# =========================================================

def main():

    print("=" * 60)

    print(
        "AI Attendance System"
    )

    print("=" * 60)

    recognition = (
        FaceRecognition()
    )

    if (
        len(
            recognition.database
        )
        == 0
    ):

        print()
        print(
            "No face embeddings found."
        )

        print()
        print(
            "Run:"
        )

        print(
            "python -m services.face_encoder"
        )

        recognition.close()

        return

    print()

    print(
        f"Loaded "
        f"{len(recognition.database)} "
        f"Student(s)"
    )

    print()

    print(
        "Starting Scheduled "
        "4-Check Attendance System..."
    )

    try:

        recognition.start()

    except KeyboardInterrupt:

        print()
        print(
            "Program stopped by user."
        )

    except Exception as error:

        print()
        print(
            "Error:",
            error
        )

    finally:

        recognition.close()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()