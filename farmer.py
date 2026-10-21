from flask import Blueprint, render_template, request, session
import sqlite3

farmer_bp = Blueprint('farmer', __name__)
DATABASE = "database/organic_trace.db"

@farmer_bp.route('/farmer_dashboard')
def dashboard():
    return render_template('dashboards/farmer_dashboard.html')

@farmer_bp.route('/add_product', methods=['POST'])
def add_product():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO products (product_name, farmer_id, harvest_date, cert_no, status) VALUES (?,?,?,?,?)",
        (request.form['product_name'], session['user_id'], request.form['harvest_date'], request.form['cert_no'], "Harvested")
    )
    conn.commit()
    conn.close()
    return "Product Added Successfully"