from flask import Flask, render_template, session

from extensions import csrf, mail
from routes.auth import auth
from routes.dashboard import dashboard
from routes.profile import profile
from routes.customer import customer
from flask_wtf.csrf import CSRFError



# Blueprints still to come:
# from routes.profile import profile
# from routes.customer import customer

app = Flask(__name__)
app.config.from_object("config.Config")

if not app.config["SECRET_KEY"]:
    raise RuntimeError("SECRET_KEY is missing. Set it in your .env file.")

csrf.init_app(app)
mail.init_app(app)

app.register_blueprint(auth)
app.register_blueprint(dashboard)
app.register_blueprint(profile)
app.register_blueprint(customer)



@app.route("/")
def home():
    return render_template("home.html")

def show_error(code, message):
    return render_template("error.html", code=code, message=message), code


@app.errorhandler(404)
def not_found(error):
    return show_error(404, "We couldn't find that page.")


@app.errorhandler(500)
def server_error(error):
    return show_error(500, "Something went wrong on our side.")


@app.errorhandler(CSRFError)
def csrf_error(error):
    return show_error(400, "Your session expired. Go back, refresh the "
                           "page and try again.")


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"

    if "user_id" in session:
        response.headers["Cache-Control"] = "no-store"

    return response

if __name__ == "__main__":
    app.run(debug=True)
