from flask import Blueprint, render_template, request, session, redirect, jsonify
import sqlite3
from datetime import datetime

exit_products_bp = Blueprint('exit_products', __name__)
DATABASE = "database/organic_trace.db"

def check_farmer():
    """Check if user is farmer"""
    if 'role' not in session or session['role'] != 'farmer':
        return False
    return True

@exit_products_bp.route('/exit-products')
def list_exit_products():
    if not check_farmer():
        return redirect('/login')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ep.id, ep.product_name, ep.product_type, ep.quantity, ep.date_created, 
               u.name, ep.status, ep.assigned_to_name
        FROM exit_products ep
        LEFT JOIN users u ON ep.created_by=u.id
        WHERE ep.created_by=? OR ep.farmer_id=?
        ORDER BY ep.date_created DESC
    ''', (session['user_id'], session['user_id']))
    products = cursor.fetchall()
    
    cursor.execute("SELECT id, name FROM users WHERE role IN ('distributor', 'retailer', 'consumer')")
    users = cursor.fetchall()
    
    conn.close()
    
    return render_template('exit_products/list.html', products=products, users=users)

@exit_products_bp.route('/exit-products/add', methods=['GET', 'POST'])
def add_exit_product():
    if not check_farmer():
        return redirect('/login')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    if request.method == 'POST':
        entry_product_id = request.form.get('entry_product_id')
        assigned_to_id = request.form.get('assigned_to_id')
        
        cursor.execute("SELECT * FROM entry_products WHERE id=?", (entry_product_id,))
        entry_product = cursor.fetchone()
        
        if not entry_product:
            conn.close()
            return redirect('/exit-products')
        
        cursor.execute("SELECT name FROM users WHERE id=?", (assigned_to_id,))
        assigned_user = cursor.fetchone()
        
        farmer_id = session['user_id'] if session['role'] == 'farmer' else None
        
        cursor.execute('''
            (product_name, product_type, quantity, unit, entry_product_id,
             assigned_to_id, assigned_to_name, date_created, created_by, 
             farmer_id, status, certification_no)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry_product[1],
            entry_product[2],
            entry_product[3],
            entry_product[4],
            entry_product_id,
            assigned_to_id,
            assigned_user[0] if assigned_user else '',
            datetime.now().strftime('%Y-%m-%d'),
            session['user_id'],
            farmer_id,
            'Assigned',
            entry_product[5]
        ))
        exit_id = cursor.lastrowid
        
        # Log to Blockchain Table
        cursor.execute('''
            INSERT INTO supply_chain (exit_product_id, product_name, timestamp, location, user_role)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            exit_id,
            entry_product[1],
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            f"Dispatched to {assigned_user[0] if assigned_user else 'Unknown'}",
            session['role']
        ))
        
        conn.commit()
        conn.close()
        
        return redirect('/exit-products')
    
    cursor.execute("SELECT id, product_name, quantity FROM entry_products WHERE created_by=? OR farmer_id=? AND status='Entry'", 
                   (session['user_id'], session['user_id']))
    entry_products = cursor.fetchall()
    
    cursor.execute("SELECT id, name FROM users WHERE role IN ('distributor', 'retailer', 'consumer')")
    users = cursor.fetchall()
    
    conn.close()
    
    return render_template('exit_products/add.html', entry_products=entry_products, users=users)

@exit_products_bp.route('/exit-products/<int:product_id>')
def view_exit_product(product_id):
    if not check_farmer():
        return redirect('/login')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ep.*, u.name FROM exit_products ep
        LEFT JOIN users u ON ep.created_by=u.id
        WHERE ep.id=?
    ''', (product_id,))
    product = cursor.fetchone()
    
    if not product:
        conn.close()
        return redirect('/exit-products')
    
    cursor.execute('''
        SELECT id, product_name, timestamp, location, user_role FROM supply_chain
        WHERE exit_product_id=?
        ORDER BY timestamp DESC
    ''', (product_id,))
    supply_chain = cursor.fetchall()
    
    conn.close()
    
    return render_template('exit_products/view.html', product=product, supply_chain=supply_chain)

@exit_products_bp.route('/exit-products/search', methods=['GET'])
def search_exit_products():
    if not check_farmer():
        return jsonify({"error": "Unauthorized"}), 403
    
    search_type = request.args.get('type', '')
    search_value = request.args.get('value', '').lower()
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    query = '''
        SELECT ep.id, ep.product_name, ep.product_type, ep.quantity, ep.date_created, 
               u.name, ep.status, ep.assigned_to_name
        FROM exit_products ep
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
        'status': p[6],
        'assigned_to': p[7]
    } for p in products])
