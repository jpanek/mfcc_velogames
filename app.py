# app.py

from flask import Flask
from hooks import before_request
from context_processors import inject_current_year 

# Import blueprints
from routes.main import main_bp


# Initialize app creation function
def create_app():
    app = Flask(__name__)

    #load settings from config.py
    app.config.from_pyfile('config.py')

    # Register blueprints
    app.register_blueprint(main_bp)
    # Register the before_request function
    app.before_request(before_request)
    app.context_processor(inject_current_year)
    return app


# This is for running the app directly
if __name__ == '__main__':
    app = create_app()  # Create the app instance
    app.run(debug=True, port=5001)