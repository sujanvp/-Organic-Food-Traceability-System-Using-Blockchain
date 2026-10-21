from flask import Blueprint, render_template, request, session, redirect, jsonify, send_file
import sqlite3
from datetime import datetime
import qrcode
import io

track_food_bp = Blueprint('track_food', __name__)
DATABASE = "database/organic_trace.db"

@track_food_bp.route('/track-food')
def track_food():
    if 'user_id' not in session:
        return redirect('/login')
    
    return render_template('track_food/search.html')

@track_food_bp.route('/track-food/search', methods=['GET', 'POST'])
def search_food():
    if 'user_id' not in session:
        return redirect('/login')
    
    search_value = request.form.get('search', '').lower() if request.method == 'POST' else request.args.get('q', '').lower()
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT DISTINCT p.id, p.product_name, p.product_type, p.status, p.date_added
        FROM products p
        WHERE p.product_name LIKE ? OR p.product_type LIKE ?
        ORDER BY p.date_added DESC
        LIMIT 20
    ''', (f"%{search_value}%", f"%{search_value}%"))
    
    products = cursor.fetchall()
    conn.close()
    
    if request.method == 'POST':
        return render_template('track_food/results.html', products=products, search_value=search_value)
    
    return jsonify([{
        'id': p[0],
        'name': p[1],
        'type': p[2],
        'status': p[3],
        'date': p[4]
    } for p in products])

@track_food_bp.route('/track-food/product/<int:product_id>')
def view_product_trace(product_id):
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.* FROM products p WHERE p.id=?
    ''', (product_id,))
    product = cursor.fetchone()
    
    if not product:
        conn.close()
        return redirect('/track-food')
    
    cursor.execute('''
        SELECT id, product_name, timestamp, location, user_role, farmer_name
        FROM supply_chain
        WHERE product_id=?
        ORDER BY timestamp ASC
    ''', (product_id,))
    supply_chain = cursor.fetchall()
    
    cursor.execute('''
        SELECT ep.*, u.name FROM entry_products ep
        LEFT JOIN users u ON ep.created_by=u.id
        WHERE ep.product_name=?
        LIMIT 1
    ''', (product[1],))
    entry_info = cursor.fetchone()
    
    conn.close()
    
    return render_template('track_food/trace.html', product=product, supply_chain=supply_chain, entry_info=entry_info)

@track_food_bp.route('/track-food/filter', methods=['GET'])
def filter_by_date():
    if 'user_id' not in session:
        return redirect('/login')
    
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    search_value = request.args.get('search', '').lower()
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    query = '''
        SELECT DISTINCT p.id, p.product_name, p.product_type, p.status, p.date_added
        FROM products p
        WHERE p.product_name LIKE ? OR p.product_type LIKE ?
    '''
    params = [f"%{search_value}%", f"%{search_value}%"]
    
    if start_date:
        query += " AND p.date_added >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND p.date_added <= ?"
        params.append(end_date)
    
    query += " ORDER BY p.date_added DESC LIMIT 20"
    
    cursor.execute(query, params)
    products = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'id': p[0],
        'name': p[1],
        'type': p[2],
        'status': p[3],
        'date': p[4]
    } for p in products])

@track_food_bp.route('/track-food/qr/<int:product_id>')
def generate_qr(product_id):
    if 'user_id' not in session:
        return redirect('/login')
        
    # Generate the tracking URL for this product
    url = request.host_url.rstrip('/') + f"/track-food/product/{product_id}"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = io.BytesIO()
    img.save(buffered,format="PNG")
    buffered.seek(0)
    
    return send_file(buffered, mimetype='image/png')
