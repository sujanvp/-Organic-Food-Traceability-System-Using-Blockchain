from flask import Blueprint, render_template, request, session, redirect, jsonify
import sqlite3
from datetime import datetime

used_today_bp = Blueprint('used_today', __name__)
DATABASE = "database/organic_trace.db"

def check_retailer_consumer():
    """Check if user is retailer or consumer"""
    if 'role' not in session or session['role'] not in ['retailer', 'consumer']:
        return False
    return True

@used_today_bp.route('/used-today')
def list_used_today():
    if not check_retailer_consumer():
        return redirect('/login')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ut.id, ut.product_name, ut.product_type, ut.quantity, ut.date_used, 
               u.name, ut.source_user
        FROM used_today ut
        LEFT JOIN users u ON ut.created_by=u.id
        WHERE ut.created_by=?
        ORDER BY ut.date_used DESC
    ''', (session['user_id'],))
    products = cursor.fetchall()
    
    cursor.execute('''
        SELECT ep.id, ep.product_name, ep.quantity FROM exit_products ep
        WHERE ep.assigned_to_id=?
        ORDER BY ep.date_created DESC
    ''', (session['user_id'],))
    available_products = cursor.fetchall()
    
    conn.close()
    
    return render_template('used_today/list.html', products=products, available_products=available_products)

@used_today_bp.route('/used-today/add', methods=['GET', 'POST'])
def add_used_today():
    if not check_retailer_consumer():
        return redirect('/login')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    if request.method == 'POST':
        exit_product_id = request.form.get('exit_product_id')
        
        cursor.execute("SELECT product_name, product_type FROM exit_products WHERE id=?", (exit_product_id,))
        product = cursor.fetchone()
        
        if product:
            cursor.execute('''
                INSERT INTO used_today 
                (product_name, product_type, quantity, unit, exit_product_id,
                 date_used, created_by, source_user)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                product[0],
                product[1],
                request.form['quantity'],
                request.form.get('unit', ''),
                exit_product_id,
                datetime.now().strftime('%Y-%m-%d'),
                session['user_id'],
                request.form.get('source_user', '')
            ))
            usage_id = cursor.lastrowid
            
            # Log to Blockchain Table
            cursor.execute('''
                INSERT INTO supply_chain (exit_product_id, product_name, timestamp, location, user_role)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                exit_product_id,
                product[0],
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                f"Consumed/Sold by {session['name']}",
                session['role']
            ))
            
            conn.commit()
        
        conn.close()
        return redirect('/used-today')
    
    cursor.execute('''
        SELECT ep.id, ep.product_name, ep.quantity FROM exit_products ep
        WHERE ep.assigned_to_id=?
        ORDER BY ep.date_created DESC
    ''', (session['user_id'],))
    available_products = cursor.fetchall()
    
    conn.close()
    
    return render_template('used_today/add.html', available_products=available_products)

@used_today_bp.route('/used-today/<int:product_id>')
def view_used_today(product_id):
    if not check_retailer_consumer():
        return redirect('/login')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ut.* FROM used_today ut
        WHERE ut.id=? AND ut.created_by=?
    ''', (product_id, session['user_id']))
    product = cursor.fetchone()
    
    if not product:
        conn.close()
        return redirect('/used-today')
    
    cursor.execute('''
        SELECT id, product_name, timestamp, location, user_role FROM supply_chain
        WHERE exit_product_id=?
        ORDER BY timestamp DESC
    ''', (product[5],))  # exit_product_id is at index 5
    supply_chain = cursor.fetchall()
    
    conn.close()
    
    return render_template('used_today/view.html', product=product, supply_chain=supply_chain)

@used_today_bp.route('/used-today/search', methods=['GET'])
def search_used_today():
    if not check_retailer_consumer():
        return jsonify({"error": "Unauthorized"}), 403
    
    search_type = request.args.get('type', '')
    search_value = request.args.get('value', '').lower()
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    query = '''
        SELECT ut.id, ut.product_name, ut.product_type, ut.quantity, ut.date_used, 
               u.name, ut.source_user
        FROM used_today ut
        LEFT JOIN users u ON ut.created_by=u.id
        WHERE ut.created_by=?
    '''
    params = [session['user_id']]
    
    if search_type == 'product' and search_value:
        query += " AND ut.product_name LIKE ?"
        params.append(f"%{search_value}%")
    elif search_type == 'date' and search_value:
        query += " AND ut.date_used = ?"
        params.append(search_value)
    elif search_type == 'user' and search_value:
        query += " AND ut.source_user LIKE ?"
        params.append(f"%{search_value}%")
    
    query += " ORDER BY ut.date_used DESC"
    
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
        'source': p[6]
    } for p in products])
