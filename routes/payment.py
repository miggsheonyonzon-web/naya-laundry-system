import os
import secrets

from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, session, url_for)

from models.payment_method import LABELS, PaymentMethod
from routes.auth import login_required

payment = Blueprint("payment", __name__, url_prefix="/payments")

MAX_QR_BYTES = 2 * 1024 * 1024

# Every real image file starts with fixed bytes, so we check those instead of
# trusting the file name the browser sends.
SIGNATURES = {
    b"\x89PNG\r\n\x1a\n": ".png",
    b"\xff\xd8\xff": ".jpg",
}


def qr_folder():
    folder = os.path.join(current_app.static_folder, "uploads", "qr")
    os.makedirs(folder, exist_ok=True)
    return folder


def detect_extension(data):
    for signature, extension in SIGNATURES.items():
        if data.startswith(signature):
            return extension
    return None


def delete_file(filename):
    if filename:
        path = os.path.join(qr_folder(), os.path.basename(filename))
        if os.path.exists(path):
            os.remove(path)


@payment.route("/settings")
@login_required
def settings():
    methods = PaymentMethod.find_all(session["user_id"])
    return render_template("payment_settings.html", methods=methods)


@payment.route("/settings/<name>/upload", methods=["POST"])
@login_required
def upload_qr(name):
    if name not in LABELS:
        abort(404)

    upload = request.files.get("qr")
    if upload is None or upload.filename == "":
        flash("Choose an image first.", "danger")
        return redirect(url_for("payment.settings"))

    data = upload.read(MAX_QR_BYTES + 1)
    if len(data) > MAX_QR_BYTES:
        flash("The image must be 2 MB or smaller.", "danger")
        return redirect(url_for("payment.settings"))

    extension = detect_extension(data)
    if extension is None:
        flash("Only PNG or JPG images are allowed.", "danger")
        return redirect(url_for("payment.settings"))

    method = PaymentMethod.find_by_name(session["user_id"], name)

    # A random name means a file can never overwrite another or guess a path.
    filename = f"{secrets.token_hex(16)}{extension}"
    with open(os.path.join(qr_folder(), filename), "wb") as handle:
        handle.write(data)

    PaymentMethod.set_qr(session["user_id"], name, filename)
    delete_file(method.qr_file)

    flash(f"{LABELS[name]} QR saved.", "success")
    return redirect(url_for("payment.settings"))


@payment.route("/settings/<name>/remove", methods=["POST"])
@login_required
def remove_qr(name):
    if name not in LABELS:
        abort(404)

    method = PaymentMethod.find_by_name(session["user_id"], name)
    PaymentMethod.set_qr(session["user_id"], name, None)
    delete_file(method.qr_file)

    flash(f"{LABELS[name]} QR removed.", "info")
    return redirect(url_for("payment.settings"))