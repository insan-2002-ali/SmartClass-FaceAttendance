from database.db import get_connection


def create_teacher_assignment_table():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teacher_assignments (

            id INT AUTO_INCREMENT PRIMARY KEY,

            teacher_id INT NOT NULL,

            subject_id INT NOT NULL,

            department_id INT NOT NULL,

            semester INT NOT NULL,

            section VARCHAR(10) NOT NULL,

            academic_year VARCHAR(20) NOT NULL,

            status ENUM('Active','Inactive') DEFAULT 'Active',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT fk_assignment_teacher
                FOREIGN KEY (teacher_id)
                REFERENCES teachers(id)
                ON DELETE CASCADE
                ON UPDATE CASCADE,

            CONSTRAINT fk_assignment_subject
                FOREIGN KEY (subject_id)
                REFERENCES subjects(id)
                ON DELETE CASCADE
                ON UPDATE CASCADE,

            CONSTRAINT fk_assignment_department
                FOREIGN KEY (department_id)
                REFERENCES departments(id)
                ON DELETE CASCADE
                ON UPDATE CASCADE

        )
    """)

    connection.commit()

    cursor.close()
    connection.close()

    print("Teacher Assignment table created successfully.")


if __name__ == "__main__":
    create_teacher_assignment_table()