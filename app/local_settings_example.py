# *****************************
# Environment specific settings
# *****************************

# DO NOT use "DEBUG = True" in production environments
import os

DEBUG = True

# DO NOT use Unsecure Secrets in production environments
# Generate a safe one with:
#     python -c "import os; print repr(os.urandom(24));"
SECRET_KEY = 'This is an UNSECURE Secret. CHANGE THIS for production environments.'

root_path = os.path.dirname(os.path.abspath(__file__))

# SQLAlchemy settings
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + root_path + '/../app.sqlite'
SQLALCHEMY_TRACK_MODIFICATIONS = False    # Avoids a SQLAlchemy Warning
JSONIFY_PRETTYPRINT_REGULAR = False
