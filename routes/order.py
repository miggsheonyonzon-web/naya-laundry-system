from decimal import Decimal, InvalidOperation
import csv
import io
from datetime import datetime
from flask import (Blueprint, Response, abort, flash, redirect,
                   render_template, request, session, url_for)

from models.customer import Customer
from models.order import SERVICES, STATUSES, Order
from routes.auth import login_required

order = Blueprint("order", __name__, url_prefix="/orders")


def read_and_validate(user_id):
    """Read the form and return (values, weight, errors)."""
    values = {
        "customer_id": request.form.get("customer_id", ""),
        "service_type": request.form.get("service_type", ""),
        "weight_kg": request.form.get("weight_kg", "").strip(),
        "notes": request.form.get("notes", "").strip(),
    }
    errors = []

    # The customer must exist AND belong to this owner.
    customer = None
    if values["customer_id"].isdigit():
        customer = Customer.find_by_id(int(values["customer_id"]), user_id)
    if customer is None:
        errors.append("Please choose one of your customers.")

    if values["service_type"] not in SERVICES:
        errors.append("Please choose a valid service.")

    weight = None
    try:
        weight = Decimal(values["weight_kg"])
        if not weight.is_finite() or not (Decimal("0.1") <= weight
                                          <= Decimal("100")):
            raise InvalidOperation
        weight = weight.quantize(Decimal("0.01"))
    except InvalidOperation:
        weight = None
        errors.append("Weight must be a number between 0.1 and 100 kg.")

    if len(values["notes"]) > 1000:
        errors.append("Notes must be 1000 characters or fewer.")

    return values, weight, errors


@order.route("/")
@login_required
def index():
    filters = read_filters()
    orders = Order.search(session["user_id"], **filters)
    total = sum((o.price for o in orders), Decimal("0"))

    return render_template("orders.html", orders=orders, filters=filters,
                           status=filters["status"], statuses=STATUSES,
                           total=total)

@order.route("/add", methods=["GET", "POST"])
@login_required
def add():
    user_id = session["user_id"]
    customers = Customer.find_all(user_id)

    if not customers:
        flash("Add a customer first, then you can create an order.", "warning")
        return redirect(url_for("customer.add"))

    if request.method == "POST":
        values, weight, errors = read_and_validate(user_id)

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("order_form.html", form=values,
                                   customers=customers, services=SERVICES)

        price = Order.calculate_price(values["service_type"], weight)
        Order.create(user_id, int(values["customer_id"]),
                     values["service_type"], weight, price, values["notes"])

        flash(f"Order created. Total: ₱{price}", "success")
        return redirect(url_for("order.index"))

    return render_template("order_form.html", form={}, customers=customers,
                           services=SERVICES) 


@order.route("/<int:order_id>/status", methods=["POST"])
@login_required
def update_status(order_id):
    record = Order.find_by_id(order_id, session["user_id"])
    if record is None:
        abort(404)

    status = request.form.get("status", "")
    if status not in STATUSES:
        flash("Invalid status.", "danger")
    else:
        Order.update_status(order_id, session["user_id"], status)
        flash(f"Order #{order_id} marked as {status}.", "success")

    return redirect(url_for("order.index"))


@order.route("/<int:order_id>/delete", methods=["POST"])
@login_required
def delete(order_id):
    record = Order.find_by_id(order_id, session["user_id"])
    if record is None:
        abort(404)

    Order.delete(order_id, session["user_id"])
    flash(f"Order #{order_id} deleted.", "info")
    return redirect(url_for("order.index"))

@order.route("/<int:order_id>")
@login_required
def detail(order_id):
    record = Order.find_by_id(order_id, session["user_id"])
    if record is None:
        abort(404)

    customer = Customer.find_by_id(record.customer_id, session["user_id"])
    return render_template("order_detail.html", order=record,
                           customer=customer)

@order.route("/<int:order_id>/paid", methods=["POST"])
@login_required
def toggle_paid(order_id):
    record = Order.find_by_id(order_id, session["user_id"])
    if record is None:
        abort(404)

    now_paid = not record.paid
    Order.mark_paid(order_id, session["user_id"], now_paid)

    state = "paid" if now_paid else "unpaid"
    flash(f"Order #{order_id} marked as {state}.", "success")
    return redirect(url_for("order.index"))


@order.route("/<int:order_id>/edit", methods=["GET", "POST"])
@login_required
def edit(order_id):
    user_id = session["user_id"]
    record = Order.find_by_id(order_id, user_id)
    if record is None:
        abort(404)

    if record.paid:
        flash("Paid orders can't be edited. Mark the order unpaid first.",
              "warning")
        return redirect(url_for("order.index"))

    customers = Customer.find_all(user_id)
    title = f"Edit order #{order_id}"

    if request.method == "POST":
        values, weight, errors = read_and_validate(user_id)

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("order_form.html", form=values,
                                   customers=customers, services=SERVICES,
                                   title=title, button="Save changes")

        price = Order.calculate_price(values["service_type"], weight)
        Order.update(order_id, user_id, int(values["customer_id"]),
                     values["service_type"], weight, price, values["notes"])

        flash(f"Order #{order_id} updated. New total: ₱{price}", "success")
        return redirect(url_for("order.index"))

    form = {
        "customer_id": str(record.customer_id),
        "service_type": record.service_type,
        "weight_kg": str(record.weight_kg),
        "notes": record.notes or "",
    }
    return render_template("order_form.html", form=form, customers=customers,
                           services=SERVICES, title=title,
                           button="Save changes")


def read_filters():
    """Read and clean the filter values from the URL."""
    filters = {
        "status": request.args.get("status", ""),
        "payment": request.args.get("payment", ""),
        "q": request.args.get("q", "").strip()[:100],
        "date_from": request.args.get("date_from", ""),
        "date_to": request.args.get("date_to", ""),
    }

    if filters["status"] not in STATUSES:
        filters["status"] = ""
    if filters["payment"] not in ("paid", "unpaid"):
        filters["payment"] = ""

    for key in ("date_from", "date_to"):
        try:
            datetime.strptime(filters[key], "%Y-%m-%d")
        except ValueError:
            filters[key] = ""

    return filters


def safe_cell(value):
    """Stop spreadsheet programs from running text as a formula."""
    text = "" if value is None else str(value)
    if text.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + text
    return text


@order.route("/export")
@login_required
def export():
    orders = Order.search(session["user_id"], **read_filters())

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Order #", "Date", "Customer", "Service", "Weight (kg)",
                     "Total", "Status", "Paid", "Notes"])

    for o in orders:
        writer.writerow([
            o.id,
            o.created_at.strftime("%Y-%m-%d %H:%M"),
            safe_cell(o.customer_name),
            safe_cell(o.service_type),
            o.weight_kg,
            o.price,
            safe_cell(o.status),
            "Yes" if o.paid else "No",
            safe_cell(o.notes),
        ])

    # The leading \ufeff makes Excel read the file as UTF-8.
    return Response(
        "\ufeff" + buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition":
                 "attachment; filename=naya_orders.csv"},
    )
