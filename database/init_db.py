
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_db_connection




def create_database():

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute("""

        CREATE TABLE IF NOT EXISTS users (

            id INT AUTO_INCREMENT PRIMARY KEY,

            user_id VARCHAR(50) UNIQUE NOT NULL,

            full_name VARCHAR(100) NOT NULL,

            password VARCHAR(255) NOT NULL,

            role ENUM('admin','teacher','student') NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )

    """)

    conn.commit()

    print("Users table created successfully.")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    create_database()