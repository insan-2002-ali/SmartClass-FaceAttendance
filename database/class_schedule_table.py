from database.db import get_connection


def create_class_schedule_table():

    connection = get_connection()
    cursor = connection.cursor()

    query = """
    CREATE TABLE IF NOT EXISTS class_schedules (

        id INT AUTO_INCREMENT PRIMARY KEY,

        class_id INT NOT NULL,

        day_of_week ENUM(
            'Sunday',
            'Monday',
            'Tuesday',
            'Wednesday',
            'Thursday',
            'Friday',
            'Saturday'
        ) NOT NULL,

        start_time TIME NOT NULL,

        end_time TIME NOT NULL,

        break_start TIME DEFAULT NULL,

        break_end TIME DEFAULT NULL,

        room_no VARCHAR(20) DEFAULT NULL,

        building VARCHAR(100) DEFAULT NULL,

        status ENUM(
            'Active',
            'Inactive'
        ) DEFAULT 'Active',

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        UNIQUE KEY unique_schedule (
            class_id,
            day_of_week,
            start_time
        ),

        CONSTRAINT fk_schedule_class
            FOREIGN KEY (class_id)
            REFERENCES classes(id)
            ON DELETE RESTRICT
            ON UPDATE CASCADE

    )
    """

    cursor.execute(query)

    connection.commit()

    cursor.close()
    connection.close()

    print(
        "Class Schedules table created successfully."
    )


if __name__ == "__main__":
    create_class_schedule_table()