from flask import Blueprint, render_template, session

from models.customer import Customer
from models.order import Order
from models.user import User
from routes.auth import login_required

dashboard = Blueprint("dashboard", __name__)


@dashboard.route("/dashboard")
@login_required
def index():
    user_id = session["user_id"]

    user = User.find_by_id(user_id)
    total_customers = Customer.count(user_id)
    recent_customers = Customer.find_recent(user_id, 5)
    order_counts = Order.count_by_status(user_id)

    return render_template("dashboard.html", user=user,
                           total_customers=total_customers,
                           recent_customers=recent_customers,
                           order_counts=order_counts)

