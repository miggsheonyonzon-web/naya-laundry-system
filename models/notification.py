from datetime import datetime

from database import get_db_connection


class Notification:
    def __init__(self, id, user_id, kind, message, customer_id=None,
                 order_id=None, is_read=0, created_at=None):
        self.id = id
        self.user_id = user_id
        self.kind = kind
        self.message = message
        self.customer_id = customer_id
        self.order_id = order_id
        self.is_read = bool(is_read)
        self.created_at = created_at

    @property
    def when(self):
        """A short 'time ago' text for the bell."""
        seconds = int((datetime.now() - self.created_at).total_seconds())
        if seconds < 60:
            return "just now"
        if seconds < 3600:
            return f"{seconds // 60} min ago"
        if seconds < 86400:
            return f"{seconds // 3600} h ago"
        return self.created_at.strftime("%b %d, %I:%M %p")

    @staticmethod
    def _fetch(query, params):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
        finally:
            cursor.close()
            connection.close()
        return [Notification(**row) for row in rows]

    @staticmethod
    def _run(query, params):
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(query, params)
            connection.commit()
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def create(user_id, kind, message, customer_id=None, order_id=None):
        Notification._run(
            "INSERT INTO notifications (user_id, kind, message, customer_id, "
            "order_id) VALUES (%s, %s, %s, %s, %s)",
            (user_id, kind, message[:255], customer_id, order_id),
        )

    @staticmethod
    def latest(user_id, limit=8):
        return Notification._fetch(
            "SELECT * FROM notifications WHERE user_id = %s "
            "ORDER BY created_at DESC, id DESC LIMIT %s",
            (user_id, limit),
        )

    @staticmethod
    def find_by_id(notification_id, user_id):
        rows = Notification._fetch(
            "SELECT * FROM notifications WHERE id = %s AND user_id = %s",
            (notification_id, user_id),
        )
        return rows[0] if rows else None

    @staticmethod
    def unread_count(user_id):
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "SELECT COUNT(*) FROM notifications "
                "WHERE user_id = %s AND is_read = 0", (user_id,))
            total = cursor.fetchone()[0]
        finally:
            cursor.close()
            connection.close()
        return total

    @staticmethod
    def mark_read(notification_id, user_id):
        Notification._run(
            "UPDATE notifications SET is_read = 1 WHERE id = %s AND user_id = %s",
            (notification_id, user_id),
        )

    @staticmethod
    def mark_all_read(user_id):
        Notification._run(
            "UPDATE notifications SET is_read = 1 WHERE user_id = %s",
            (user_id,),
        )