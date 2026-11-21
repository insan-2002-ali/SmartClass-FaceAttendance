from database.db import get_connection


def create_attendance_table():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (

            id INT AUTO_INCREMENT PRIMARY KEY,

            student_id VARCHAR(50) NOT NULL,

            subject_id INT NOT NULL,

            teacher_id INT NOT NULL,

            attendance_date DATE NOT NULL,

            entry_time DATETIME NOT NULL,

            exit_time DATETIME NULL,

            status ENUM('Present','Absent','Late') DEFAULT 'Present',

            confidence FLOAT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    cursor.close()
    connection.close()


if __name__ == "__main__":
    create_attendance_table()
    print("Attendance table created successfully.")