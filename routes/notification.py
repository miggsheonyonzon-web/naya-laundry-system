from flask import (Blueprint, abort, redirect, render_template, session,
                   url_for)

from models.notification import Notification
from models.order import Order
from models.supply import Supply
from routes.auth import login_required

notification = Blueprint("notification", __name__, url_prefix="/notifications")

DROPDOWN_LIMIT = 8


# ---------- Activity: saved when something happens ----------

def amount_text(record):
    """'2 piece(s) of Comforters' or '3.5 kg of General clothing'."""
    if record.pieces:
        return f"{record.pieces} piece(s) of {record.service_type}"
    return f"{record.weight_kg} kg of {record.service_type}"


def notify_new_order(user_id, order_id):
    record = Order.find_by_id(order_id, user_id)
    if record is None:
        return
    Notification.create(
        user_id, "order_new",
        f"New order #{record.id} for {record.customer_name}: "
        f"{amount_text(record)}, ₱{record.price}",
        record.customer_id, record.id)


def notify_status(user_id, record, status):
    if record.status == status:
        return  # nothing really changed
    Notification.create(
        user_id, "status",
        f"Order #{record.id} for {record.customer_name} marked as {status}.",
        record.customer_id, record.id)


def notify_paid(user_id, record, paid):
    if paid:
        message = f"{record.customer_name} paid order #{record.id} (₱{record.price})."
    else:
        message = (f"Payment removed from order #{record.id} "
                   f"for {record.customer_name}.")
    Notification.create(user_id, "paid", message, record.customer_id,
                        record.id)


# ---------- Needs attention: worked out fresh on every page ----------

def live_alerts(user_id):
    alerts = []

    for item in Supply.forecast(user_id):
        name = item["supply"].name
        if item["status"] == "out":
            alerts.append({
                "kind": "restock",
                "url": url_for("supply.index"),
                "text": f"{name} is out of stock. Restock now.",
            })
        elif item["status"] == "low":
            alerts.append({
                "kind": "restock",
                "url": url_for("supply.index"),
                "text": (f"{name} is running low and runs out on "
                         f"{item['runout'].strftime('%b %d')}. "
                         "Time to restock."),
            })

    for row in Order.stale_orders(user_id):
        days = row["days"]
        unit = "day" if days == 1 else "days"
        if row["status"] == "Ready":
            text = (f"Order #{row['id']} for {row['customer_name']} has been "
                    f"Ready for {days} {unit}. Mark it Picked up?")
        else:
            text = (f"Order #{row['id']} for {row['customer_name']} is still "
                    f"{row['status']} after {days} {unit}. "
                    "Did you forget to update it?")
        alerts.append({
            "kind": "remind",
            "url": url_for("order.index", customer_id=row["customer_id"]),
            "text": text,
        })

    return alerts


def build_notification_context(user_id):
    """The values every page needs to draw the bell."""
    alerts = live_alerts(user_id)
    unread = Notification.unread_count(user_id)
    return {
        "nav_alerts": alerts,
        "nav_notifications": Notification.latest(user_id, DROPDOWN_LIMIT),
        "nav_unread": unread,
        "nav_badge": unread + len(alerts),
    }


# ---------- Pages ----------

@notification.route("/")
@login_required
def index():
    items = Notification.latest(session["user_id"], 50)
    return render_template("notifications.html", items=items)


@notification.route("/<int:notification_id>/open", methods=["POST"])
@login_required
def open_notification(notification_id):
    item = Notification.find_by_id(notification_id, session["user_id"])
    if item is None:
        abort(404)

    Notification.mark_read(notification_id, session["user_id"])

    if item.customer_id:
        return redirect(url_for("order.index", customer_id=item.customer_id))
    return redirect(url_for("order.index"))


@notification.route("/read-all", methods=["POST"])
@login_required
def read_all():
    Notification.mark_all_read(session["user_id"])
    return redirect(url_for("notification.index"))