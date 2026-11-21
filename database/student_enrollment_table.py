from database.db import get_db_connection


def create_student_enrollment_table():

    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
    CREATE TABLE IF NOT EXISTS student_enrollments (

        id INT AUTO_INCREMENT PRIMARY KEY,

        student_id INT NOT NULL,

        teacher_assignment_id INT NOT NULL,

        status ENUM('Active','Inactive')
        DEFAULT 'Active',

        created_at TIMESTAMP
        DEFAULT CURRENT_TIMESTAMP,

        CONSTRAINT fk_enrollment_student
            FOREIGN KEY (student_id)
            REFERENCES students(id)
            ON DELETE CASCADE
            ON UPDATE CASCADE,

        CONSTRAINT fk_enrollment_assignment
            FOREIGN KEY (teacher_assignment_id)
            REFERENCES teacher_assignments(id)
            ON DELETE CASCADE
            ON UPDATE CASCADE,

        UNIQUE(student_id, teacher_assignment_id)

    )
    """

    cursor.execute(query)

    connection.commit()

    cursor.close()
    connection.close()

    print("Student Enrollment table created successfully.")


if __name__ == "__main__":

    create_student_enrollment_table()