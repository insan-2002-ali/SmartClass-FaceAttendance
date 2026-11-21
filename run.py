
import os
import atexit

from app import create_app
from services.scheduler import attendance_scheduler


app = create_app()


if __name__ == "__main__":

    # Register scheduler shutdown for the actual Flask process.
    # Scheduler will NOT start automatically.
    if (
        not app.debug
        or os.environ.get("WERKZEUG_RUN_MAIN") == "true"
    ):
        atexit.register(
            attendance_scheduler.shutdown
        )

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
