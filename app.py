from flask import Flask
from flask_sslify import SSLify

app = Flask(__name__)
sslify = SSLify(app)


@app.route('/')
def hello_world():
    return 'Hello World!'


if __name__ == '__main__':
    import os
    app.debug = bool(os.environ.get('WEB_DEBUG'))
    app.run()
