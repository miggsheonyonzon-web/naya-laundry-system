import calendar
import math
from datetime import date, datetime, timedelta
from decimal import Decimal

from flask import Blueprint, render_template, request, session

from models.order import Order
from routes.auth import login_required

volume = Blueprint("volume", __name__, url_prefix="/volume")


def read_month():
    """Read ?month=YYYY-MM from the URL, falling back to this month."""
    text = request.args.get("month", "")
    try:
        return datetime.strptime(text, "%Y-%m").date().replace(day=1)
    except ValueError:
        return date.today().replace(day=1)


def month_bounds(first_day):
    last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    return first_day, last_day


def total_between(totals, start, end):
    """Add up kg and orders for the days between start and end."""
    kg = Decimal("0")
    orders = 0
    for day, item in totals.items():
        if start <= day <= end:
            kg += item["kg"]
            orders += item["orders"]
    return kg, orders


def current_summary(user_id):
    """kg and order counts for today, this week (Sun-Sat) and this month."""
    today = date.today()
    week_start = today - timedelta(days=(today.weekday() + 1) % 7)
    week_end = week_start + timedelta(days=6)
    month_start, month_end = month_bounds(today.replace(day=1))

    totals = Order.daily_totals(user_id, min(week_start, month_start),
                                max(week_end, month_end))

    today_kg, today_orders = total_between(totals, today, today)
    week_kg, week_orders = total_between(totals, week_start, week_end)
    month_kg, month_orders = total_between(totals, month_start, month_end)

    return {
        "today": {"kg": today_kg, "orders": today_orders},
        "week": {"kg": week_kg, "orders": week_orders},
        "month": {"kg": month_kg, "orders": month_orders},
        "avg_per_day": month_kg / today.day,
    }


@volume.route("/")
@login_required
def index():
    user_id = session["user_id"]
    first_day = read_month()
    first_day, last_day = month_bounds(first_day)

    weeks = calendar.Calendar(firstweekday=6).monthdatescalendar(
        first_day.year, first_day.month)
    totals = Order.daily_totals(user_id, weeks[0][0], weeks[-1][-1])

    # Shade each day from 1 (light) to 4 (dark) compared with the busiest day.
    max_kg = max((item["kg"] for item in totals.values()),
                 default=Decimal("0"))
    levels = {}
    for day, item in totals.items():
        if max_kg > 0 and item["kg"] > 0:
            levels[day] = max(1, math.ceil(float(item["kg"] / max_kg) * 4))

    rows = [(week, total_between(totals, week[0], week[-1])) for week in weeks]
    month_kg, month_orders = total_between(totals, first_day, last_day)

    in_month = {day: item for day, item in totals.items()
                if first_day <= day <= last_day}
    busiest = max(in_month.items(), key=lambda pair: pair[1]["kg"],
                  default=None)

    prev_month = (first_day - timedelta(days=1)).replace(day=1)
    next_month = (last_day + timedelta(days=1)).replace(day=1)

    return render_template("volume.html", summary=current_summary(user_id),
                           rows=rows, totals=totals, levels=levels,
                           month=first_day, month_kg=month_kg,
                           month_orders=month_orders, busiest=busiest,
                           prev_month=prev_month, next_month=next_month,
                           today=date.today())