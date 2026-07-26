from config import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

sql = """
INSERT INTO users (user_id, full_name, password, role)
VALUES (%s, %s, %s, %s)
"""

values = (
    "admin",
    "System Administrator",
    "admin123",
    "admin"
)

try:
    cursor.execute(sql, values)
    conn.commit()
    print("Admin user created successfully.")
except Exception as e:
    print(e)

cursor.close()
conn.close()