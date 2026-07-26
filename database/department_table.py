from config import get_db_connection


def create_department_table():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS departments (

        id INT AUTO_INCREMENT PRIMARY KEY,

        department_code VARCHAR(20) UNIQUE NOT NULL,

        department_name VARCHAR(100) NOT NULL,

        description TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)

    conn.commit()

    cursor.close()
    conn.close()

    print("Departments table created successfully.")


if __name__ == "__main__":
    create_department_table()