from flask import Blueprint, render_template, session, redirect
import sqlite3

dashboard_bp = Blueprint('dashboard', __name__)
DATABASE = "database/organic_trace.db"

@dashboard_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session or 'role' not in session:
        return redirect('/login')
    
    role = session['role']
    user_id = session['user_id']
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    
    # Get role-specific stats
    stats = {}
    
    if role == 'farmer':
        cursor.execute("SELECT COUNT(*) FROM products WHERE farmer_id=?", (user_id,))
        stats['products'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM entry_products WHERE farmer_id=?", (user_id,))
        stats['entries'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM exit_products WHERE farmer_id=?", (user_id,))
        stats['exits'] = cursor.fetchone()[0]
    

    
    elif role == 'distributor':
        cursor.execute("SELECT COUNT(*) FROM shipments WHERE distributor_id=?", (user_id,))
        stats['total_shipments'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM shipments WHERE distributor_id=? AND status=?", (user_id, 'In Transit'))
        stats['in_transit'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM shipments WHERE distributor_id=? AND status=?", (user_id, 'Delivered'))
        stats['delivered'] = cursor.fetchone()[0]
        # Fallbacks
        stats['received'] = stats['total_shipments']
        stats['distributed'] = stats['delivered']
    
    elif role == 'retailer':
        cursor.execute("SELECT COUNT(*) FROM exit_products WHERE assigned_to_id=?", (user_id,))
        stats['inventory'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM used_today WHERE created_by=?", (user_id,))
        stats['used_today'] = cursor.fetchone()[0]
    
    elif role == 'consumer':
        cursor.execute("SELECT COUNT(*) FROM used_today WHERE created_by=?", (user_id,))
        stats['products_used'] = cursor.fetchone()[0]    

    elif role == 'admin':
        cursor.execute("SELECT COUNT(*) FROM users")
        stats['total_users'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM products")
        stats['total_products'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM supply_chain")
        stats['total_transactions'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users WHERE status='pending'")
        stats['pending_users'] = cursor.fetchone()[0]
    
    conn.close()
    
    return render_template(f'dashboards/{role}_dashboard.html', user=user, stats=stats)

@dashboard_bp.route('/dashboard/farmer')
def farmer_dashboard():
    if 'user_id' not in session or session['role'] != 'farmer':
        return redirect('/login')
    return redirect('/dashboard')



@dashboard_bp.route('/dashboard/distributor')
def distributor_dashboard():
    if 'user_id' not in session or session['role'] != 'distributor':
        return redirect('/login')
    return redirect('/dashboard')

@dashboard_bp.route('/dashboard/retailer')
def retailer_dashboard():
    if 'user_id' not in session or session['role'] != 'retailer':
        return redirect('/login')
    return redirect('/dashboard')

@dashboard_bp.route('/dashboard/consumer')
def consumer_dashboard():
    if 'user_id' not in session or session['role'] != 'consumer':
        return redirect('/login')
    return redirect('/dashboard')

@dashboard_bp.route('/dashboard/admin')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect('/login')
    return redirect('/dashboard')
