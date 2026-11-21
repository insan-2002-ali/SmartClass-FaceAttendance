
from flask import Flask
from config import Config
import os


def create_app():

    app = Flask(
        __name__,
        template_folder=os.path.join(
            os.path.dirname(__file__),
            "../templates"
        ),
        static_folder=os.path.join(
            os.path.dirname(__file__),
            "../static"
        )
    )

    # ==========================
    # Configuration
    # ==========================

    app.config["SECRET_KEY"] = Config.SECRET_KEY
    app.config["UPLOAD_FOLDER"] = Config.UPLOAD_FOLDER
    app.config["FACE_DATA_FOLDER"] = Config.FACE_DATA_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = Config.MAX_CONTENT_LENGTH

    # ==========================
    # Create Required Folders
    # ==========================

    os.makedirs(
        app.config["UPLOAD_FOLDER"],
        exist_ok=True
    )

    os.makedirs(
        app.config["FACE_DATA_FOLDER"],
        exist_ok=True
    )

    # ==========================
    # Import Blueprints
    # ==========================

    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.admission_year import admission_year_bp
    from app.routes.program import program_bp
    from app.routes.department import department_bp
    from app.routes.teacher import teacher_bp
    from app.routes.subject import subject_bp
    from app.routes.teacher_assignment import teacher_assignment_bp
    from app.routes.student import student_bp
    from app.routes.student_enrollment import student_enrollment_bp
    from app.routes.face_registration import face_registration_bp
    from app.routes.class_schedule import class_schedule_bp
    from app.routes.attendance_settings import attendance_settings_bp

    # ==========================
    # Register Blueprints
    # ==========================

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admission_year_bp)
    app.register_blueprint(program_bp)
    app.register_blueprint(department_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(subject_bp)
    app.register_blueprint(teacher_assignment_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(student_enrollment_bp)
    app.register_blueprint(face_registration_bp)
    app.register_blueprint(class_schedule_bp)
    app.register_blueprint(attendance_settings_bp)

    return app
