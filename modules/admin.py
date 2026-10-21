from flask import Blueprint, render_template, request, session, redirect, jsonify
import sqlite3
from datetime import datetime

admin_bp = Blueprint('admin', __name__)
DATABASE = "database/organic_trace.db"

def check_admin():
    if 'user_id' not in session or session.get('role') != 'admin':
        return False
    return True

@admin_bp.route('/admin/users')
def manage_users():
    if not check_admin():
        return redirect('/login')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, role, status FROM users WHERE role != 'admin' ORDER BY id DESC")
    users = cursor.fetchall()
    conn.close()
    
    return render_template('admin/manage_users.html', users=users)

@admin_bp.route('/admin/users/<int:user_id>/<action>', methods=['POST'])
def update_user_status(user_id, action):
    if not check_admin():
        return jsonify({"error": "Unauthorized"}), 403
    
    if action not in ['approve', 'reject']:
        return jsonify({"error": "Invalid action"}), 400
        
    status = 'approved' if action == 'approve' else 'rejected'
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status=? WHERE id=?", (status, user_id))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "status": status})

@admin_bp.route('/admin/transactions')
def monitor_transactions():
    if not check_admin():
        return redirect('/login')
        
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Get recent supply chain activities
    cursor.execute('''
        SELECT id, product_name, timestamp, location, user_role, farmer_name 
        FROM supply_chain 
        ORDER BY timestamp DESC
    ''')
    transactions = cursor.fetchall()
    conn.close()
    
    return render_template('admin/transactions.html', transactions=transactions)
