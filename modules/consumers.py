from flask import Blueprint, render_template, request, session
import sqlite3

consumers_bp = Blueprint('consumers', __name__)
DATABASE = "database/organic_trace.db"

@consumers_bp.route('/consumer_dashboard')
def dashboard():
    return render_template('dashboards/consumer_dashboard.html')

@consumers_bp.route('/track_product', methods=['GET'])
def track_product():
    product_id = request.args.get('product_id')
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE product_id=?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    return {"product": product}

@consumers_bp.route('/view_history', methods=['GET'])
def view_history():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM products WHERE consumer_id=? ORDER BY date_purchased DESC",
        (session['user_id'],)
    )
    products = cursor.fetchall()
    conn.close()
    return {"products": products}
