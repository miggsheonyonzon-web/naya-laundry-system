import re

from flask import (Blueprint, flash, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import generate_password_hash

from models.user import User
from routes.auth import EMAIL_PATTERN, NAME_PATTERN, login_required

profile = Blueprint("profile", __name__)


@profile.route("/profile", methods=["GET", "POST"])
@login_required
def index():
    user = User.find_by_id(session["user_id"])

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip().lower()

        errors = []

        if not NAME_PATTERN.fullmatch(first_name):
            errors.append("First name must be 1-50 letters.")
        if not NAME_PATTERN.fullmatch(last_name):
            errors.append("Last name must be 1-50 letters.")
        if len(email) > 100 or not EMAIL_PATTERN.fullmatch(email):
            errors.append("Please enter a valid email address.")
        else:
            other = User.find_by_email(email)
            if other and other.id != user.id:
                errors.append("That email is used by another account.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("profile.html", form=request.form)

        User.update_profile(user.id, first_name, last_name, email)
        session["user_name"] = f"{first_name} {last_name}"
        flash("Profile updated.", "success")
        return redirect(url_for("profile.index"))

    form = {"first_name": user.first_name, "last_name": user.last_name,
            "email": user.email}
    return render_template("profile.html", form=form)


@profile.route("/profile/password", methods=["GET", "POST"])
@login_required
def change_password():
    user = User.find_by_id(session["user_id"])

    if request.method == "POST":
        current = request.form.get("current_password", "")
        new = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")

        errors = []

        if not user.check_password(current):
            errors.append("Your current password is incorrect.")
        if len(new) < 8:
            errors.append("New password must be at least 8 characters.")
        if not (re.search(r"[a-z]", new) and re.search(r"[A-Z]", new)
                and re.search(r"\d", new)):
            errors.append("New password needs an uppercase letter, a "
                          "lowercase letter and a number.")
        if new != confirm:
            errors.append("New passwords do not match.")
        if current and new == current:
            errors.append("New password must be different from the old one.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("change_password.html")

        User.update_password(user.id, generate_password_hash(new))
        flash("Password changed.", "success")
        return redirect(url_for("profile.index"))

    return render_template("change_password.html")