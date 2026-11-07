import calendar
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from flask import (Blueprint, abort, flash, redirect, render_template,
                   request, session, url_for)

from models.supply import LOW_DAYS, Supply
from routes.auth import login_required

supply = Blueprint("supply", __name__, url_prefix="/supplies")


def read_month():
    """Read ?month=YYYY-MM from the URL, falling back to this month."""
    text = request.args.get("month", "")
    try:
        return datetime.strptime(text, "%Y-%m").date().replace(day=1)
    except ValueError:
        return date.today().replace(day=1)


def build_calendar(first_day, forecasts):
    """Return the weeks of the month and a dictionary of dated markers."""
    events = {}

    for item in forecasts:
        runout = item["runout"]
        if runout is None:
            continue

        name = item["supply"].name
        events.setdefault(runout, []).append((f"{name} runs out", "danger"))

        order_by = runout - timedelta(days=LOW_DAYS)
        if order_by >= date.today():
            events.setdefault(order_by, []).append((f"Order {name}", "warning"))

    weeks = calendar.Calendar(firstweekday=6).monthdatescalendar(
        first_day.year, first_day.month)
    return weeks, events


@supply.route("/")
@login_required
def index():
    forecasts = Supply.forecast(session["user_id"])
    first_day = read_month()
    weeks, events = build_calendar(first_day, forecasts)

    prev_month = (first_day - timedelta(days=1)).replace(day=1)
    next_month = (first_day + timedelta(days=32)).replace(day=1)

    return render_template("supplies.html", forecasts=forecasts, weeks=weeks,
                           events=events, month=first_day,
                           prev_month=prev_month, next_month=next_month,
                           today=date.today())


@supply.route("/<int:supply_id>/stock", methods=["POST"])
@login_required
def update_stock(supply_id):
    record = Supply.find_by_id(supply_id, session["user_id"])
    if record is None:
        abort(404)

    try:
        counted = Decimal(request.form.get("counted_kg", ""))
        grams = Decimal(request.form.get("grams_per_kg", ""))

        if not (counted.is_finite() and grams.is_finite()):
            raise InvalidOperation
        if not (Decimal("0") <= counted <= Decimal("100000")):
            raise InvalidOperation
        if not (Decimal("1") <= grams <= Decimal("500")):
            raise InvalidOperation
    except InvalidOperation:
        flash("Stock must be between 0 and 100,000 kg, and the usage rate "
              "between 1 and 500 grams per kg of laundry.", "danger")
        return redirect(url_for("supply.index"))

    Supply.update_stock(supply_id, session["user_id"],
                        counted.quantize(Decimal("0.01")),
                        grams.quantize(Decimal("0.01")))
    flash(f"{record.name} stock updated.", "success")
    return redirect(url_for("supply.index"))