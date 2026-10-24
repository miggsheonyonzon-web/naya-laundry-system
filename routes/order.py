from decimal import Decimal, InvalidOperation

from flask import (Blueprint, abort, flash, redirect, render_template,
                   request, session, url_for)

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
    status = request.args.get("status", "")
    if status not in STATUSES:
        status = ""

    orders = Order.find_all(session["user_id"], status)
    return render_template("orders.html", orders=orders, status=status,
                           statuses=STATUSES)


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