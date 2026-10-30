from decimal import Decimal

from database import get_db_connection

# Sample rates in pesos per kg. Confirm the real rates with your client.
SERVICES = {
    "Wash & Fold": 50,
    "Wash, Dry & Fold": 70,
    "Dry Clean": 150,
    "Bedding & Comforters": 200,
}

STATUSES = ["Received", "Washing", "Ready", "Picked up"]


class Order:
    def __init__(self, id, user_id, customer_id, service_type, weight_kg,
                 price, status, notes=None, created_at=None, updated_at=None,
                 customer_name=None, paid=0, paid_at=None):
        self.id = id
        self.user_id = user_id
        self.customer_id = customer_id
        self.service_type = service_type
        self.weight_kg = weight_kg
        self.price = price
        self.status = status
        self.notes = notes
        self.created_at = created_at
        self.updated_at = updated_at
        self.customer_name = customer_name
        self.paid = bool(paid)
        self.paid_at = paid_at

    @staticmethod
    def calculate_price(service_type, weight):
        rate = SERVICES[service_type]
        return (Decimal(str(weight)) * rate).quantize(Decimal("0.01"))

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
        return [Order(**row) for row in rows]

    @staticmethod
    def find_all(user_id, status=""):
        query = ("SELECT o.*, c.full_name AS customer_name FROM orders o "
                 "JOIN customers c ON c.id = o.customer_id "
                 "WHERE o.user_id = %s")
        params = [user_id]

        if status:
            query += " AND o.status = %s"
            params.append(status)

        query += " ORDER BY o.created_at DESC, o.id DESC"
        return Order._fetch_all(query, tuple(params))

    @staticmethod
    def find_by_id(order_id, user_id):
     rows = Order._fetch_all(
        "SELECT o.*, c.full_name AS customer_name FROM orders o "
        "JOIN customers c ON c.id = o.customer_id "
        "WHERE o.id = %s AND o.user_id = %s",
        (order_id, user_id),
    )
     return rows[0] if rows else None
    @staticmethod
    def count_by_status(user_id):
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "SELECT status, COUNT(*) FROM orders WHERE user_id = %s "
                "GROUP BY status", (user_id,))
            counts = dict(cursor.fetchall())
        finally:
            cursor.close()
            connection.close()
        return {status: counts.get(status, 0) for status in STATUSES}

    @staticmethod
    def create(user_id, customer_id, service_type, weight_kg, price, notes):
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO orders (user_id, customer_id, service_type, "
                "weight_kg, price, notes) VALUES (%s, %s, %s, %s, %s, %s)",
                (user_id, customer_id, service_type, weight_kg, price,
                 notes or None),
            )
            connection.commit()
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def update_status(order_id, user_id, status):
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "UPDATE orders SET status = %s WHERE id = %s AND user_id = %s",
                (status, order_id, user_id),
            )
            connection.commit()
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def delete(order_id, user_id):
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM orders WHERE id = %s AND user_id = %s",
                           (order_id, user_id))
            connection.commit()
        finally:
            cursor.close()
            connection.close()
    @staticmethod
    def find_by_customer(customer_id, user_id):
        return Order._fetch_all(
            "SELECT o.*, c.full_name AS customer_name FROM orders o "
            "JOIN customers c ON c.id = o.customer_id "
            "WHERE o.customer_id = %s AND o.user_id = %s "
            "ORDER BY o.created_at DESC, o.id DESC",
            (customer_id, user_id),
        )

    @staticmethod
    def mark_paid(order_id, user_id, paid):
        connection = get_db_connection()
        cursor = connection.cursor()
        flag = 1 if paid else 0
        try:
            cursor.execute(
                "UPDATE orders SET paid = %s, "
                "paid_at = IF(%s = 1, NOW(), NULL) "
                "WHERE id = %s AND user_id = %s",
                (flag, flag, order_id, user_id),
            )
            connection.commit()
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def revenue_summary(user_id):
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "SELECT "
                "COALESCE(SUM(CASE WHEN paid = 1 THEN price END), 0), "
                "COALESCE(SUM(CASE WHEN paid = 0 THEN price END), 0), "
                "COALESCE(SUM(CASE WHEN paid = 1 "
                "AND DATE(paid_at) = CURDATE() THEN price END), 0) "
                "FROM orders WHERE user_id = %s",
                (user_id,),
            )
            collected, unpaid, today = cursor.fetchone()
        finally:
            cursor.close()
            connection.close()
        return {"collected": collected, "unpaid": unpaid, "today": today}

    @staticmethod
    def update(order_id, user_id, customer_id, service_type, weight_kg,
               price, notes):
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "UPDATE orders SET customer_id = %s, service_type = %s, "
                "weight_kg = %s, price = %s, notes = %s "
                "WHERE id = %s AND user_id = %s",
                (customer_id, service_type, weight_kg, price, notes or None,
                 order_id, user_id),
            )
            connection.commit()
        finally:
            cursor.close()
            connection.close()
