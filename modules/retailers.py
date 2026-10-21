from flask import Blueprint, render_template, request, session
import sqlite3

retailers_bp = Blueprint('retailers', __name__)
DATABASE = "database/organic_trace.db"

@retailers_bp.route('/retailer_dashboard')
def dashboard():
    return render_template('dashboards/retailer_dashboard.html')

@retailers_bp.route('/stock_product', methods=['POST'])
def stock_product():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO inventory (product_id, retailer_id, quantity, date_received, status) VALUES (?,?,?,?,?)",
        (request.form['product_id'], session['user_id'], request.form['quantity'], request.form['date_received'], "In Stock")
    )
    conn.commit()
    conn.close()
    return "Product Stocked Successfully"
