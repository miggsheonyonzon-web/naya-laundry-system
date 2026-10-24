from database import get_db_connection


class PendingRegistration:
    def __init__(self, id, first_name, last_name, email, password, otp,
                 expires_at):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password
        self.otp = otp
        self.expires_at = expires_at

    @staticmethod
    def save(first_name, last_name, email, password_hash, otp, expires_at):
        """Store a new pending registration (replaces any older one for the email)."""
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM pending_registrations WHERE email = %s",
                           (email,))
            cursor.execute(
                "INSERT INTO pending_registrations "
                "(first_name, last_name, email, password, otp, expires_at) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (first_name, last_name, email, password_hash, otp, expires_at),
            )
            connection.commit()
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def find_by_email(email):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM pending_registrations WHERE email = %s",
                           (email,))
            row = cursor.fetchone()
        finally:
            cursor.close()
            connection.close()
        return PendingRegistration(**row) if row else None

    @staticmethod
    def delete_by_email(email):
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM pending_registrations WHERE email = %s",
                           (email,))
            connection.commit()
        finally:
            cursor.close()
            connection.close()
