from database import get_db_connection

# Stored name -> label shown on screen.
LABELS = {
    "GCash": "GCash",
    "InstaPay": "Bank QR Ph / InstaPay",
}


class PaymentMethod:
    def __init__(self, id, user_id, name, qr_file=None, updated_at=None):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.qr_file = qr_file
        self.updated_at = updated_at

    @property
    def label(self):
        return LABELS.get(self.name, self.name)

    @staticmethod
    def ensure_defaults(user_id):
        """Create one row per wallet the first time it's needed."""
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            for name in LABELS:
                cursor.execute(
                    "INSERT IGNORE INTO payment_methods (user_id, name) "
                    "VALUES (%s, %s)",
                    (user_id, name),
                )
            connection.commit()
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def find_all(user_id):
        PaymentMethod.ensure_defaults(user_id)

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT * FROM payment_methods WHERE user_id = %s "
                "ORDER BY name",
                (user_id,),
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()
            connection.close()
        return [PaymentMethod(**row) for row in rows]

    @staticmethod
    def find_by_name(user_id, name):
        for method in PaymentMethod.find_all(user_id):
            if method.name == name:
                return method
        return None

    @staticmethod
    def set_qr(user_id, name, qr_file):
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "UPDATE payment_methods SET qr_file = %s "
                "WHERE user_id = %s AND name = %s",
                (qr_file, user_id, name),
            )
            connection.commit()
        finally:
            cursor.close()
            connection.close()