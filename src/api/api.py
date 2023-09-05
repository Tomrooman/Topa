from flask import Flask
from gevent.pywsgi import WSGIServer
from dotenv import dotenv_values

config = dotenv_values(".env")
app = Flask(__name__)


@app.get("/")
def hello_world():
    return "<p>Hello, World!</p>"


if __name__ == '__main__':
    print('please run main.py')
    # Production
    http_server = WSGIServer(('', 5000), app)
    http_server.serve_forever()
