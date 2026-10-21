from flask import Blueprint, render_template, request, session, redirect, jsonify
import sqlite3
from datetime import datetime

products_bp = Blueprint('products', __name__)
DATABASE = "database/organic_trace.db"

def check_access():
    """Check if user is farmer"""
    if 'role' not in session or session['role'] != 'farmer':
        return False
    return True

@products_bp.route('/products')
def manage_products():
    if not check_access():
        return redirect('/login')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM products WHERE farmer_id=? ORDER BY id DESC",
        (session.get('user_id'),)
    )
    products = cursor.fetchall()
    conn.close()
    
    return render_template('products/manage_products.html', products=products)

@products_bp.route('/products/search', methods=['GET'])
def search_products():
    if not check_access():
        return jsonify({"error": "Unauthorized"}), 403
    
    search_query = request.args.get('q', '').lower()
    filter_type = request.args.get('type', '')
    filter_status = request.args.get('status', '')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    query = "SELECT * FROM products WHERE farmer_id=?"
    params = [session.get('user_id')]
    
    if search_query:
        query += " AND product_name LIKE ?"
        params.append(f"%{search_query}%")
    
    if filter_type:
        query += " AND product_type=?"
        params.append(filter_type)
    
    if filter_status:
        query += " AND status=?"
        params.append(filter_status)
    
    query += " ORDER BY id DESC"
    
    cursor.execute(query, params)
    products = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        "id": p[0],
        "name": p[1],
        "type": p[2] if len(p) > 2 else "",
        "status": p[3] if len(p) > 3 else "",
        "date": p[4] if len(p) > 4 else ""
    } for p in products])

@products_bp.route('/products/add', methods=['GET', 'POST'])
def add_product():
    if not check_access():
        return redirect('/login')
    
    if request.method == 'POST':
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        user_id = session['user_id']
        farmer_id = user_id if session['role'] == 'farmer' else None
        
        cursor.execute('''
            INSERT INTO products (product_name, product_type, farmer_id, 
                                 date_added, status, certification_no, quantity, unit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.form['product_name'],
            request.form['product_type'],
            farmer_id,
            datetime.now().strftime('%Y-%m-%d'),
            'Active',
            request.form.get('certification_no', ''),
            request.form.get('quantity', 0),
            request.form.get('unit', ''),
        ))
        product_id = cursor.lastrowid
        
        # Log to Blockchain Table (supply_chain)
        cursor.execute('''
            INSERT INTO supply_chain (product_id, product_name, timestamp, location, user_role, farmer_name)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            product_id,
            request.form['product_name'],
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Farm / Facility Origin',
            session['role'],
            session['name'] if session['role'] == 'farmer' else None
        ))
        
        conn.commit()
        conn.close()
        
        return redirect('/products')
    
    return render_template('products/add_product.html')

@products_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
def edit_product(product_id):
    if not check_access():
        return redirect('/login')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM products WHERE id=?", (product_id,))
    product = cursor.fetchone()
    
    if not product:
        conn.close()
        return redirect('/products')
    
    # Check if user is the owner
    if product[2] != session['user_id'] and product[3] != session['user_id']:
        conn.close()
        return redirect('/products')
    
    if request.method == 'POST':
        cursor.execute('''
            UPDATE products SET product_name=?, product_type=?, status=?, 
                              certification_no=?, quantity=?, unit=?
            WHERE id=?
        ''', (
            request.form['product_name'],
            request.form['product_type'],
            request.form['status'],
            request.form.get('certification_no', ''),
            request.form.get('quantity', product[7]),
            request.form.get('unit', product[8]),
            product_id
        ))
        conn.commit()
        conn.close()
        
        return redirect('/products')
    
    conn.close()
    return render_template('products/edit_product.html', product=product)

@products_bp.route('/products/<int:product_id>/delete', methods=['POST'])
def delete_product(product_id):
    if not check_access():
        return jsonify({"error": "Unauthorized"}), 403
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM products WHERE id=?", (product_id,))
    product = cursor.fetchone()
    
    if not product:
        conn.close()
        return jsonify({"error": "Product not found"}), 404
    
    # Check if user is the owner
    if product[2] != session['user_id'] and product[3] != session['user_id']:
        conn.close()
        return jsonify({"error": "Unauthorized"}), 403
    
    cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})

@products_bp.route('/products/<int:product_id>')
def view_product(product_id):
    if not check_access():
        return redirect('/login')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT p.*, u.name 
        FROM products p
        LEFT JOIN users u ON p.farmer_id=u.id
        WHERE p.id=?
    ''', (product_id,))
    product = cursor.fetchone()
    conn.close()
    
    if not product:
        return redirect('/products')
    
    return render_template('products/view_product.html', product=product)
