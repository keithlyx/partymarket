# THIS APP.PY IS TO RENDER THE HTML TEMPLATES
from os import environ

from user_application import app

if __name__ == '__main__':
    debug = environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=5902, debug=debug)
