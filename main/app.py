# THIS APP.PY IS TO RENDER THE HTML TEMPLATES
from user_application import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5902, debug=True)
