from database.db import get_connection


def create_subject_table():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (

            id INT AUTO_INCREMENT PRIMARY KEY,

            subject_code VARCHAR(20) UNIQUE NOT NULL,

            subject_name VARCHAR(100) NOT NULL,

            credit FLOAT NOT NULL,

            semester INT NOT NULL,

            department_id INT NOT NULL,

            status ENUM('Active','Inactive') DEFAULT 'Active',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            CONSTRAINT fk_subject_department
            FOREIGN KEY (department_id)
            REFERENCES departments(id)
            ON DELETE CASCADE
            ON UPDATE CASCADE

        )
    """)

    connection.commit()

    cursor.close()
    connection.close()

    print("Subject table created successfully.")


if __name__ == "__main__":

    create_subject_table()