from config import get_db_connection


def create_student_table():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (

        id INT AUTO_INCREMENT PRIMARY KEY,

        student_id VARCHAR(30) UNIQUE NOT NULL,

        full_name VARCHAR(100) NOT NULL,

        department VARCHAR(100),

        semester VARCHAR(20),

        email VARCHAR(100),

        phone VARCHAR(30),

        gender ENUM('Male','Female'),

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)

    conn.commit()

    cursor.close()
    conn.close()

    print("Students table created successfully.")


if __name__ == "__main__":
    create_student_table()