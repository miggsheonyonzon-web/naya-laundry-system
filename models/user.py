from werkzeug.security import check_password_hash

from database import get_db_connection


class User:
    def __init__(self, id, first_name, last_name, email, password,
                 role="owner", created_at=None):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password
        self.role = role
        self.created_at = created_at

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def check_password(self, plain_password):
        return check_password_hash(self.password, plain_password)

    @staticmethod
    def find_by_email(email):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            row = cursor.fetchone()
        finally:
            cursor.close()
            connection.close()
        return User(**row) if row else None

    @staticmethod
    def find_by_id(user_id):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            row = cursor.fetchone()
        finally:
            cursor.close()
            connection.close()
        return User(**row) if row else None

    @staticmethod
    def create(first_name, last_name, email, password_hash, role="owner"):
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (first_name, last_name, email, password, role) "
                "VALUES (%s, %s, %s, %s, %s)",
                (first_name, last_name, email, password_hash, role),
            )
            connection.commit()
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def update_profile(user_id, first_name, last_name, email):
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "UPDATE users SET first_name = %s, last_name = %s, email = %s "
                "WHERE id = %s",
                (first_name, last_name, email, user_id),
            )
            connection.commit()
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def update_password(user_id, password_hash):
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("UPDATE users SET password = %s WHERE id = %s",
                        (password_hash, user_id))
            connection.commit()
        finally:
            cursor.close()
            connection.close()
