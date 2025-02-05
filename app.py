from flask import Flask, render_template
from middle import middle_bp  # Assuming middle.py is a Flask Blueprint
from top import top_bp  # Assuming top.py is a Flask Blueprint
from bottom import bottom_bp  # Assuming bottom.py is a Flask Blueprint

app = Flask(__name__)

# Register the blueprints
app.register_blueprint(middle_bp, url_prefix='/middle')
app.register_blueprint(top_bp, url_prefix='/top')
app.register_blueprint(bottom_bp, url_prefix='/bottom')

@app.route('/')
def dashboard():
    """Render the main dashboard with all sections."""
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)
