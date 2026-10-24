from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect

# Created here (not in app.py) so route files can import them
# without causing a circular import.
csrf = CSRFProtect()
mail = Mail()
