from flask import Flask
from routes.mandatory import mandatory_bp
from routes.optional import optional_bp
from routes.export import export_bp
from routes.auth import auth_bp
from routes.apps import apps_bp
from routes.queues import queues_bp
import logging

app = Flask(__name__)

# Disable verbose Flask HTTP request logging (only show errors)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app.register_blueprint(mandatory_bp, url_prefix="/mandatory")
app.register_blueprint(optional_bp, url_prefix="/optional")
app.register_blueprint(export_bp, url_prefix="/export")
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(apps_bp, url_prefix="/fetch-apps")
app.register_blueprint(queues_bp, url_prefix="/fetch-queues")

if __name__ == "__main__":
    app.run(debug=False)
