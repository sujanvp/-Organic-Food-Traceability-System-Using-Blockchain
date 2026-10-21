from flask import Blueprint, render_template, request, session, redirect, jsonify
import sqlite3
from datetime import datetime

entry_products_bp = Blueprint('entry_products', __name__)
DATABASE = "database/organic_trace.db"

def check_farmer():
    """Check if user is farmer"""
    if 'role' not in session or session['role'] != 'farmer':
        return False
    return True

@entry_products_bp.route('/entry-products')
def list_entry_products():
    if not check_farmer():
        return redirect('/login')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ep.id, ep.product_name, ep.product_type, ep.quantity, ep.date_created, 
               u.name, ep.status, ep.certification_no
        FROM entry_products ep
        LEFT JOIN users u ON ep.created_by=u.id
        WHERE ep.created_by=? OR ep.farmer_id=?
        ORDER BY ep.date_created DESC
    ''', (session['user_id'], session['user_id']))
    products = cursor.fetchall()
    conn.close()
    
    return render_template('entry_products/list.html', products=products)

@entry_products_bp.route('/entry-products/add', methods=['GET', 'POST'])
def add_entry_product():
    if not check_farmer():
        return redirect('/login')
    
    if request.method == 'POST':
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        farmer_id = session['user_id'] if session['role'] == 'farmer' else None
        
        cursor.execute('''
            (product_name, product_type, quantity, unit, certification_no, 
             date_created, created_by, farmer_id, status, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.form['product_name'],
            request.form['product_type'],
            request.form['quantity'],
            request.form['unit'],
            request.form.get('certification_no', ''),
            datetime.now().strftime('%Y-%m-%d'),
            session['user_id'],
            farmer_id,
            'Entry',
            request.form.get('description', '')
        ))
        entry_id = cursor.lastrowid
        
        # Log to Blockchain Table
        cursor.execute('''
            INSERT INTO supply_chain (entry_product_id, product_name, timestamp, location, user_role)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            entry_id,
            request.form['product_name'],
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Intake / Processing Center',
            session['role']
        ))
        
        conn.commit()
        conn.close()
        
        return redirect('/entry-products')
    
    return render_template('entry_products/add.html')

@entry_products_bp.route('/entry-products/<int:product_id>')
def view_entry_product(product_id):
    if not check_farmer():
        return redirect('/login')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ep.*, u.name FROM entry_products ep
        LEFT JOIN users u ON ep.created_by=u.id
        WHERE ep.id=?
    ''', (product_id,))
    product = cursor.fetchone()
    
    if not product:
        conn.close()
        return redirect('/entry-products')
    
    cursor.execute('''
        SELECT id, product_name, timestamp, location FROM supply_chain
        WHERE entry_product_id=?
        ORDER BY timestamp DESC
    ''', (product_id,))
    supply_chain = cursor.fetchall()
    
    conn.close()
    
    return render_template('entry_products/view.html', product=product, supply_chain=supply_chain)

@entry_products_bp.route('/entry-products/search', methods=['GET'])
def search_entry_products():
    if not check_farmer():
        return jsonify({"error": "Unauthorized"}), 403
    
    search_type = request.args.get('type', '')
    search_value = request.args.get('value', '').lower()
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    query = '''
        SELECT ep.id, ep.product_name, ep.product_type, ep.quantity, ep.date_created, 
               u.name, ep.status, ep.certification_no
        FROM entry_products ep
        LEFT JOIN users u ON ep.created_by=u.id
        WHERE (ep.created_by=? OR ep.farmer_id=?)
    '''
    params = [session['user_id'], session['user_id']]
    
    if search_type == 'product' and search_value:
        query += " AND ep.product_name LIKE ?"
        params.append(f"%{search_value}%")
    elif search_type == 'date' and search_value:
        query += " AND ep.date_created = ?"
        params.append(search_value)
    elif search_type == 'user' and search_value:
        query += " AND u.name LIKE ?"
        params.append(f"%{search_value}%")
    
    query += " ORDER BY ep.date_created DESC"
    
    cursor.execute(query, params)
    products = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'id': p[0],
        'name': p[1],
        'type': p[2],
        'quantity': p[3],
        'date': p[4],
        'user': p[5],
        'status': p[6]
    } for p in products])
