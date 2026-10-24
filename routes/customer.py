import re

from flask import (Blueprint, abort, flash, redirect, render_template,
request, session, url_for)

from models.customer import Customer
from routes.auth import login_required

customer = Blueprint("customer", __name__, url_prefix="/customers")

NAME_PATTERN = re.compile(r"[A-Za-zÀ-ÿ .'-]{1,100}")
PHONE_PATTERN = re.compile(r"[0-9+()\- ]{7,20}")
EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def read_and_validate(user_id, customer_id=None):
    """Read the form, clean it, and return (values, errors)."""
    values = {
        "full_name": request.form.get("full_name", "").strip(),
        "phone": request.form.get("phone", "").strip(),
        "email": request.form.get("email", "").strip().lower(),
        "address": request.form.get("address", "").strip(),
        "notes": request.form.get("notes", "").strip(),
    }
    errors = []

    if not NAME_PATTERN.fullmatch(values["full_name"]):
        errors.append("Full name must be 1-100 letters.")

    if not PHONE_PATTERN.fullmatch(values["phone"]):
        errors.append("Phone must be 7-20 characters (digits, +, -, spaces, "
                      "parentheses).")
    elif Customer.phone_exists(user_id, values["phone"], customer_id):
        errors.append("You already have a customer with that phone number.")

    if values["email"] and (len(values["email"]) > 100
                            or not EMAIL_PATTERN.fullmatch(values["email"])):
        errors.append("Please enter a valid email address.")

    if len(values["address"]) > 255:
        errors.append("Address must be 255 characters or fewer.")

    if len(values["notes"]) > 1000:
        errors.append("Notes must be 1000 characters or fewer.")

    return values, errors


@customer.route("/")
@login_required
def index():
    search = request.args.get("q", "").strip()
    customers = Customer.find_all(session["user_id"], search)
    return render_template("customers.html", customers=customers, search=search)


@customer.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        values, errors = read_and_validate(session["user_id"])

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("customer_form.html", form=values,
                                   title="Add customer")

        Customer.create(session["user_id"], values["full_name"],
                        values["phone"], values["email"], values["address"],
                        values["notes"])
        flash("Customer added.", "success")
        return redirect(url_for("customer.index"))

    return render_template("customer_form.html", form={}, title="Add customer")


@customer.route("/<int:customer_id>/edit", methods=["GET", "POST"])
@login_required
def edit(customer_id):
    record = Customer.find_by_id(customer_id, session["user_id"])
    if record is None:
        abort(404)

    if request.method == "POST":
        values, errors = read_and_validate(session["user_id"], customer_id)

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("customer_form.html", form=values,
                                   title="Edit customer")

        Customer.update(customer_id, session["user_id"], values["full_name"],
                        values["phone"], values["email"], values["address"],
                        values["notes"])
        flash("Customer updated.", "success")
        return redirect(url_for("customer.index"))

    return render_template("customer_form.html", form=record.to_dict(),
                           title="Edit customer")


@customer.route("/<int:customer_id>/delete", methods=["POST"])
@login_required
def delete(customer_id):
    record = Customer.find_by_id(customer_id, session["user_id"])
    if record is None:
        abort(404)

    Customer.delete(customer_id, session["user_id"])
    flash("Customer deleted.", "info")
    return redirect(url_for("customer.index"))
