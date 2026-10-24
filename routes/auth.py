import hmac
import re
import secrets
from datetime import datetime, timedelta
from functools import wraps
from time import time

from flask import (Blueprint, flash, redirect, render_template, request,
                   session, url_for)
from flask_mail import Message
from werkzeug.security import generate_password_hash

from extensions import mail
from models.pending_registration import PendingRegistration
from models.user import User

auth = Blueprint("auth", __name__)

OTP_MINUTES = 10
NAME_PATTERN = re.compile(r"[A-Za-zÀ-ÿ .'-]{1,50}")
EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
MAX_ATTEMPTS = 5
LOCK_SECONDS = 300
failed_logins = {}  # email -> (number of failures, time of last failure)


def is_locked(email):
    record = failed_logins.get(email)
    if record is None:
        return False

    count, last_failure = record
    if time() - last_failure > LOCK_SECONDS:
        failed_logins.pop(email, None)
        return False

    return count >= MAX_ATTEMPTS


def record_failure(email):
    count, _ = failed_logins.get(email, (0, 0))
    failed_logins[email] = (count + 1, time())


def clear_failures(email):
    failed_logins.pop(email, None)


def login_required(view):
    """Protect a route: redirect to login if nobody is signed in."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped


def validate_registration(first_name, last_name, email, password, confirm):
    errors = []

    if not NAME_PATTERN.fullmatch(first_name):
        errors.append("First name must be 1-50 letters.")
    if not NAME_PATTERN.fullmatch(last_name):
        errors.append("Last name must be 1-50 letters.")
    if len(email) > 100 or not EMAIL_PATTERN.fullmatch(email):
        errors.append("Please enter a valid email address.")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if not (re.search(r"[a-z]", password) and re.search(r"[A-Z]", password)
            and re.search(r"\d", password)):
        errors.append("Password needs an uppercase letter, a lowercase letter "
                      "and a number.")
    if password != confirm:
        errors.append("Passwords do not match.")

    return errors


def send_otp_email(email, first_name, otp):
    message = Message(
        subject="NAYA Bubble Laundry - Your verification code",
        recipients=[email],
        body=(
            f"Hi {first_name},\n\n"
            f"Your NAYA verification code is: {otp}\n"
            f"It expires in {OTP_MINUTES} minutes.\n\n"
            "If you did not register, you can ignore this email."
        ),
    )
    mail.send(message)


@auth.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        errors = validate_registration(first_name, last_name, email,
                                       password, confirm)

        if not errors and User.find_by_email(email):
            errors.append("That email is already registered.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("register.html", form=request.form)

        otp = f"{secrets.randbelow(1_000_000):06d}"
        expires_at = datetime.now() + timedelta(minutes=OTP_MINUTES)

        PendingRegistration.save(first_name, last_name, email,
                                 generate_password_hash(password), otp,
                                 expires_at)

        try:
            send_otp_email(email, first_name, otp)
        except Exception:
            PendingRegistration.delete_by_email(email)
            flash("We could not send the verification email. "
                  "Check the MAIL settings in your .env file.", "danger")
            return render_template("register.html", form=request.form)

        session["pending_email"] = email
        flash("We sent a 6-digit code to your email.", "info")
        return redirect(url_for("auth.verify_otp"))

    return render_template("register.html", form={})


@auth.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    email = session.get("pending_email")
    if not email:
        return redirect(url_for("auth.register"))

    if request.method == "POST":
        submitted = request.form.get("otp", "").strip()
        pending = PendingRegistration.find_by_email(email)

        if pending is None:
            session.pop("pending_email", None)
            flash("Registration not found. Please register again.", "danger")
            return redirect(url_for("auth.register"))

        if datetime.now() > pending.expires_at:
            PendingRegistration.delete_by_email(email)
            session.pop("pending_email", None)
            flash("Your code expired. Please register again.", "danger")
            return redirect(url_for("auth.register"))

        if not hmac.compare_digest(submitted, pending.otp):
            flash("Incorrect code. Please try again.", "danger")
            return render_template("verify_otp.html", email=email)

        User.create(pending.first_name, pending.last_name, pending.email,
                    pending.password)
        PendingRegistration.delete_by_email(email)
        session.pop("pending_email", None)

        flash("Account verified! You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("verify_otp.html", email=email)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if is_locked(email):
            flash("Too many failed attempts. Please wait 5 minutes and "
                  "try again.", "danger")
            return render_template("login.html", email=email)

        user = User.find_by_email(email)

        if user is None or not user.check_password(password):
            record_failure(email)
            flash("Invalid email or password.", "danger")
            return render_template("login.html", email=email)

        clear_failures(email)
        session.clear()
        session.permanent = True
        session["user_id"] = user.id
        session["user_name"] = user.get_full_name()

        return redirect(url_for("dashboard.index"))

    return render_template("login.html", email="")


@auth.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
