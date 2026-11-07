from datetime import date, timedelta
from decimal import Decimal

from database import get_db_connection

# Starting values only. Confirm the real rates with your client.
DEFAULTS = {"Detergent": Decimal("50"), "Fabcon": Decimal("25")}
WINDOW_DAYS = 30
LOW_DAYS = 7


class Supply:
    def __init__(self, id, user_id, name, counted_kg, counted_at,
                 grams_per_kg):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.counted_kg = counted_kg
        self.counted_at = counted_at
        self.grams_per_kg = grams_per_kg

    @staticmethod
    def ensure_defaults(user_id):
        """Create the Detergent and Fabcon rows the first time they're needed."""
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            for name, grams in DEFAULTS.items():
                cursor.execute(
                    "INSERT IGNORE INTO supplies (user_id, name, grams_per_kg) "
                    "VALUES (%s, %s, %s)",
                    (user_id, name, grams),
                )
            connection.commit()
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def find_all(user_id):
        Supply.ensure_defaults(user_id)

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT * FROM supplies WHERE user_id = %s ORDER BY name",
                (user_id,),
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()
            connection.close()
        return [Supply(**row) for row in rows]

    @staticmethod
    def find_by_id(supply_id, user_id):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT * FROM supplies WHERE id = %s AND user_id = %s",
                (supply_id, user_id),
            )
            row = cursor.fetchone()
        finally:
            cursor.close()
            connection.close()
        return Supply(**row) if row else None

    @staticmethod
    def update_stock(supply_id, user_id, counted_kg, grams_per_kg):
        """Save a new count. The count date resets to now."""
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "UPDATE supplies SET counted_kg = %s, grams_per_kg = %s, "
                "counted_at = NOW() WHERE id = %s AND user_id = %s",
                (counted_kg, grams_per_kg, supply_id, user_id),
            )
            connection.commit()
        finally:
            cursor.close()
            connection.close()

    @staticmethod
    def laundry_kg_since(user_id, start):
        """Total kg of laundry in orders created at or after `start`."""
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "SELECT COALESCE(SUM(weight_kg), 0) FROM orders "
                "WHERE user_id = %s AND created_at >= %s",
                (user_id, start),
            )
            total = cursor.fetchone()[0]
        finally:
            cursor.close()
            connection.close()
        return Decimal(total)

    @staticmethod
    def average_daily_laundry_kg(user_id):
        """Average kg of laundry per day over the last 30 days."""
        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT MIN(created_at) FROM orders "
                           "WHERE user_id = %s", (user_id,))
            first_order = cursor.fetchone()[0]
        finally:
            cursor.close()
            connection.close()

        if first_order is None:
            return Decimal("0")

        # A shop with only 5 days of history is averaged over 5 days, not 30.
        history_days = (date.today() - first_order.date()).days + 1
        days = max(1, min(WINDOW_DAYS, history_days))

        start = date.today() - timedelta(days=days - 1)
        total = Supply.laundry_kg_since(user_id, start)
        return total / days

    @staticmethod
    def forecast(user_id):
        """One dictionary per supply: stock, usage and run-out date."""
        supplies = Supply.find_all(user_id)
        daily_laundry = Supply.average_daily_laundry_kg(user_id)
        today = date.today()
        results = []

        for supply in supplies:
            # kg of supply needed for each kg of laundry
            per_kg = supply.grams_per_kg / 1000

            used_since_count = (
                Supply.laundry_kg_since(user_id, supply.counted_at) * per_kg)
            remaining = max(supply.counted_kg - used_since_count, Decimal("0"))

            daily_use = daily_laundry * per_kg
            capacity = remaining / per_kg if per_kg > 0 else Decimal("0")

            days_left = None
            runout = None
            if daily_use > 0:
                days_left = remaining / daily_use
                runout = today + timedelta(days=int(days_left))

            if remaining <= 0:
                status = "out"
            elif days_left is None:
                status = "unknown"
            elif days_left <= LOW_DAYS:
                status = "low"
            else:
                status = "ok"

            results.append({
                "supply": supply,
                "remaining": remaining,
                "daily_use": daily_use,
                "weekly_use": daily_use * 7,
                "monthly_use": daily_use * 30,
                "capacity_kg": capacity,
                "days_left": days_left,
                "runout": runout,
                "status": status,
            })

        return results