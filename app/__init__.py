from flask import Flask
from flask_bootstrap import Bootstrap
from flask_socketio import SocketIO
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

import eventlet
eventlet.monkey_patch()

# where should I move this normally ?
async_mode = None

app = Flask(__name__)
app.config.from_object(Config)

bootstrap = Bootstrap(app)
socketio = SocketIO(app, async_mode='eventlet')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


from app import routes, models
