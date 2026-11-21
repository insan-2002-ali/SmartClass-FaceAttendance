from database.db import get_db_connection


def create_student_table():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (

        id INT AUTO_INCREMENT PRIMARY KEY,

        student_id VARCHAR(30) UNIQUE NOT NULL,

        full_name VARCHAR(100) NOT NULL,

        email VARCHAR(100) UNIQUE,

        phone VARCHAR(30),

        gender ENUM(
            'Male',
            'Female',
            'Other'
        ) NOT NULL,

        department_id INT NOT NULL,

        admission_year_id INT NOT NULL,

        semester VARCHAR(20) NOT NULL,

        section VARCHAR(20) NOT NULL,

        profile_photo VARCHAR(255),

        password VARCHAR(255) NOT NULL,

        status ENUM(
            'Active',
            'Inactive'
        ) DEFAULT 'Active',

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (department_id)
            REFERENCES departments(id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT,

        FOREIGN KEY (admission_year_id)
            REFERENCES admission_years(id)
            ON UPDATE CASCADE
            ON DELETE RESTRICT

    )
    """)

    conn.commit()

    cursor.close()
    conn.close()

    print("Students table created successfully.")


if __name__ == "__main__":
    create_student_table()