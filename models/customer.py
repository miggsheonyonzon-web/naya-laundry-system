from database import get_db_connection


class Customer:
    def __init__(self, id, user_id, full_name, phone, email=None, address=None,
                 notes=None, created_at=None):
        self.id = id
        self.user_id = user_id
        self.full_name = full_name
        self.phone = phone
        self.email = email
        self.address = address
        self.notes = notes
        self.created_at = created_at

    def to_dict(self):
        return {
            "full_name": self.full_name,
            "phone": self.phone,
            "email": self.email or "",
            "address": self.address or "",
            "notes": self.notes or "",
        }

    # Every query below is filtered by user_id, so an owner can only
    # ever see and change their own customers.

    @staticmethod
    def _fetch_all(query, params):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
        finally:
            cursor.close()
            connection.close()
        return [Customer(**row) for row in rows]

    @staticmethod
    def find_all(user_id, search=""):
        if search:
            like = f"%{search}%"
            return Customer._fetch_all(
                "SELECT * FROM customers WHERE user_id = %s "
                "AND (full_name LIKE %s OR phone LIKE %s) "
                "ORDER BY created_at DESC, id DESC",
                (user_id, like, like),
            )
        return Customer._fetch_all(
            "SELECT * FROM customers WHERE user_id = %s "
            "ORDER BY created_at DESC, id DESC",
            (user_id,),
        )

    @staticmethod
    def find_recent(user_id, limit=5):
        return Customer._fetch_all(
            "SELECT * FROM customers WHERE user_id = %s "
            "ORDER BY created_at DESC, id DESC LIMIT %s",
            (user_id, limit),
        )

    @staticmethod
    def find_by_id(customer_id, user_id):
        rows = Customer._fetch_all(
            "SELECT * FROM customers WHERE id = %s AND user_id = %s",
            (customer_id, user_id),
        )
        return rows[0] if rows else None

    @staticmethod
    def phone_exists(user_id, phone, exclude_id=None):
        rows = Customer._fetch_all(
            "SELECT * FROM customers WHERE user_id = %s AND phone = %s",
            (user_id, phone),
        )
        return any(row.id != exclude_id for row in rows)

    @staticmethod
    def count(user_id):
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM customers WHERE user_id = %s",
                           (user_id,))
            total = cursor.fetchone()[0]
        finally:
            cursor.close()
            connection.close()
        return total

    @staticmethod
    def create(user_id, full_name, phone, email, address, notes):
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO customers (user_id, full_name, phone, email, "
                "address, notes) VALUES (%s, %s, %s, %s, %s, %s)",
                (user_id, full_name, phone, email or None, address or None,
                 notes or None),
            )
            connection.commit()
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def update(customer_id, user_id, full_name, phone, email, address, notes):
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "UPDATE customers SET full_name = %s, phone = %s, email = %s, "
                "address = %s, notes = %s WHERE id = %s AND user_id = %s",
                (full_name, phone, email or None, address or None,
                 notes or None, customer_id, user_id),
            )
            connection.commit()
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def delete(customer_id, user_id):
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM customers WHERE id = %s AND user_id = %s",
                           (customer_id, user_id))
            connection.commit()
        finally:
            cursor.close()
            connection.close()
