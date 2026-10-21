from flask import Blueprint, render_template, request, session, redirect, jsonify
import sqlite3
from datetime import datetime

distributors_bp = Blueprint('distributors', __name__)
DATABASE = "database/organic_trace.db"

def check_distributor():
    """Check if user is distributor"""
    if 'role' not in session or session['role'] != 'distributor':
        return False
    return True

def update_blockchain_ledger(shipment_id, action, details):
    """Update blockchain ledger in supply_chain table"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Get shipment details
    cursor.execute('''
        SELECT ps.packaging_info_id FROM shipments ps WHERE ps.id=?
    ''', (shipment_id,))
    result = cursor.fetchone()
    
    if result:
        cursor.execute('''
            INSERT INTO supply_chain 
            (timestamp, location, user_role, farmer_name)
            VALUES (?, ?, ?, ?)
        ''', (
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Distribution Center',
            'distributor',
        ))
        conn.commit()
    
    conn.close()

# Route: Distributor Dashboard
@distributors_bp.route('/distributor_dashboard')
def dashboard():
    if not check_distributor():
        return redirect('/login')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Count stats
    cursor.execute('SELECT COUNT(*) FROM shipments WHERE distributor_id=?', (session['user_id'],))
    total_shipments = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM shipments WHERE distributor_id=? AND status=?', 
                   (session['user_id'], 'In Transit'))
    in_transit = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM shipments WHERE distributor_id=? AND status=?', 
                   (session['user_id'], 'Delivered'))
    delivered = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM storage_conditions WHERE shipment_id IN (SELECT id FROM shipments WHERE distributor_id=?)', 
                   (session['user_id'],))
    storage_records = cursor.fetchone()[0]
    
    conn.close()
    
    return render_template('dashboards/distributor_dashboard.html', 
                         total_shipments=total_shipments,
                         in_transit=in_transit,
                         delivered=delivered,
                         storage_records=storage_records)

# Route: Accept shipment from farmer
@distributors_bp.route('/accept-shipment', methods=['GET', 'POST'])
def accept_shipment():
    if not check_distributor():
        return redirect('/login')
    
    if request.method == 'POST':
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Generate shipment number
        shipment_number = f"SHIP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        try:
            cursor.execute('''
                INSERT INTO shipments
                (shipment_number, exit_product_id, farmer_id, distributor_id, 
                 shipment_date, expected_delivery_date, status, origin_location, 
                 destination_location, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                shipment_number,
                request.form['exit_product_id'],
                request.form['farmer_id'],
                session['user_id'],
                datetime.now().strftime('%Y-%m-%d'),
                request.form['expected_delivery_date'],
                'Accepted',
                request.form['origin_location'],
                request.form['destination_location'],
                request.form.get('notes', '')
            ))
            
            conn.commit()
            
            # Update blockchain
            shipment_id = cursor.lastrowid
            update_blockchain_ledger(shipment_id, 'SHIPMENT_ACCEPTED', 'Shipment accepted from farmer')
            
            conn.close()
            return jsonify({"success": True, "message": f"Shipment {shipment_number} accepted successfully"})
        except Exception as e:
            conn.close()
            return jsonify({"success": False, "error": str(e)}), 400
    
    # GET request: Fetch available exit_products from farmers
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ep.id, ep.product_name, ep.quantity, u.name, ep.date_created
        FROM exit_products ep
        LEFT JOIN users u ON ep.farmer_id=u.id
        WHERE ep.status='Assigned' AND ep.assigned_to_id=?
        ORDER BY ep.date_created DESC
    ''', (session['user_id'],))
    available_shipments = cursor.fetchall()
    conn.close()
    
    return render_template('distributors/accept_shipment.html', available_shipments=available_shipments)

# Route: List shipments
@distributors_bp.route('/shipments')
def list_shipments():
    if not check_distributor():
        return redirect('/login')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.id, s.shipment_number, ep.product_name, s.status, s.shipment_date,
               s.expected_delivery_date, u.name
        FROM shipments s
        LEFT JOIN exit_products ep ON s.exit_product_id=ep.id
        LEFT JOIN users u ON s.farmer_id=u.id
        WHERE s.distributor_id=?
        ORDER BY s.shipment_date DESC
    ''', (session['user_id'],))
    shipments = cursor.fetchall()
    conn.close()
    
    return render_template('distributors/list_shipments.html', shipments=shipments)

# Route: View shipment details
@distributors_bp.route('/shipments/<int:shipment_id>')
def view_shipment(shipment_id):
    if not check_distributor():
        return redirect('/login')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.*, u.name FROM shipments s
        LEFT JOIN users u ON s.farmer_id=u.id
        WHERE s.id=? AND s.distributor_id=?
    ''', (shipment_id, session['user_id']))
    shipment = cursor.fetchone()
    
    if not shipment:
        conn.close()
        return redirect('/shipments')
    
    # Get transport details
    cursor.execute('''
        SELECT id, transport_mode, vehicle_number, transporter_name, driver_name,
               driver_contact, route, departure_time, estimated_arrival_time, actual_arrival_time
        FROM transport_details
        WHERE shipment_id=?
    ''', (shipment_id,))
    transport_details = cursor.fetchall()
    
    # Get storage conditions
    cursor.execute('''
        SELECT id, warehouse_location, storage_type, temperature, humidity,
               light_conditions, ventilation_status, record_date, record_time
        FROM storage_conditions
        WHERE shipment_id=?
        ORDER BY record_date DESC
    ''', (shipment_id,))
    storage_records = cursor.fetchall()
    
    # Get delivery tracking
    cursor.execute('''
        SELECT id, status, status_update_date, status_update_time, location,
               recipient_name, delivery_proof, remarks
        FROM delivery_tracking
        WHERE shipment_id=?
        ORDER BY status_update_date DESC
    ''', (shipment_id,))
    delivery_history = cursor.fetchall()
    
    conn.close()
    
    return render_template('distributors/view_shipment.html',
                         shipment=shipment,
                         transport_details=transport_details,
                         storage_records=storage_records,
                         delivery_history=delivery_history)

# Route: Add transport details
@distributors_bp.route('/add-transport', methods=['GET', 'POST'])
def add_transport():
    if not check_distributor():
        return redirect('/login')
    
    if request.method == 'POST':
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO transport_details
                (shipment_id, transport_mode, vehicle_number, transporter_name, driver_name,
                 driver_contact, route, departure_time, estimated_arrival_time, distance_km,
                 fuel_consumption, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                request.form['shipment_id'],
                request.form['transport_mode'],
                request.form['vehicle_number'],
                request.form['transporter_name'],
                request.form.get('driver_name', ''),
                request.form.get('driver_contact', ''),
                request.form.get('route', ''),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                request.form.get('estimated_arrival_time', ''),
                request.form.get('distance_km', ''),
                request.form.get('fuel_consumption', ''),
                request.form.get('notes', '')
            ))
            
            conn.commit()
            
            # Update shipment status
            cursor.execute('UPDATE shipments SET status=? WHERE id=?', 
                         ('In Transit', request.form['shipment_id']))
            conn.commit()
            
            # Update blockchain
            update_blockchain_ledger(request.form['shipment_id'], 'TRANSPORT_DETAILS', 
                                   f"Transport initiated: {request.form['transport_mode']}")
            
            conn.close()
            return jsonify({"success": True, "message": "Transport details added successfully"})
        except Exception as e:
            conn.close()
            return jsonify({"success": False, "error": str(e)}), 400
    
    # GET request
    shipment_id = request.args.get('shipment_id')
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT shipment_number FROM shipments WHERE id=?', (shipment_id,))
    shipment = cursor.fetchone()
    conn.close()
    
    return render_template('distributors/add_transport.html', shipment=shipment, shipment_id=shipment_id)

# Route: Add storage conditions
@distributors_bp.route('/add-storage', methods=['GET', 'POST'])
def add_storage():
    if not check_distributor():
        return redirect('/login')
    
    if request.method == 'POST':
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO storage_conditions
                (shipment_id, warehouse_location, storage_type, temperature, humidity,
                 light_conditions, ventilation_status, security_measures, record_date, record_time, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                request.form['shipment_id'],
                request.form['warehouse_location'],
                request.form['storage_type'],
                request.form.get('temperature', ''),
                request.form.get('humidity', ''),
                request.form.get('light_conditions', ''),
                request.form.get('ventilation_status', ''),
                request.form.get('security_measures', ''),
                datetime.now().strftime('%Y-%m-%d'),
                datetime.now().strftime('%H:%M:%S'),
                request.form.get('notes', '')
            ))
            
            conn.commit()
            
            # Update blockchain
            update_blockchain_ledger(request.form['shipment_id'], 'STORAGE_CONDITIONS', 
                                   f"Storage recorded: {request.form['warehouse_location']}")
            
            conn.close()
            return jsonify({"success": True, "message": "Storage conditions recorded successfully"})
        except Exception as e:
            conn.close()
            return jsonify({"success": False, "error": str(e)}), 400
    
    # GET request
    shipment_id = request.args.get('shipment_id')
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT shipment_number FROM shipments WHERE id=?', (shipment_id,))
    shipment = cursor.fetchone()
    conn.close()
    
    return render_template('distributors/add_storage.html', shipment=shipment, shipment_id=shipment_id)

# Route: Update delivery status
@distributors_bp.route('/update-delivery', methods=['GET', 'POST'])
def update_delivery():
    if not check_distributor():
        return redirect('/login')
    
    if request.method == 'POST':
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO delivery_tracking
                (shipment_id, status, status_update_date, status_update_time, location,
                 recipient_name, recipient_contact, delivery_proof, signature_required, remarks, updated_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                request.form['shipment_id'],
                request.form['status'],
                datetime.now().strftime('%Y-%m-%d'),
                datetime.now().strftime('%H:%M:%S'),
                request.form.get('location', ''),
                request.form.get('recipient_name', ''),
                request.form.get('recipient_contact', ''),
                request.form.get('delivery_proof', ''),
                request.form.get('signature_required') == 'on',
                request.form.get('remarks', ''),
                session['user_id']
            ))
            
            conn.commit()
            
            # Update shipment status
            cursor.execute('UPDATE shipments SET status=? WHERE id=?', 
                         (request.form['status'], request.form['shipment_id']))
            conn.commit()
            
            # Update blockchain
            update_blockchain_ledger(request.form['shipment_id'], 'DELIVERY_UPDATE', 
                                   f"Delivery status updated: {request.form['status']}")
            
            conn.close()
            return jsonify({"success": True, "message": "Delivery status updated successfully"})
        except Exception as e:
            conn.close()
            return jsonify({"success": False, "error": str(e)}), 400
    
    # GET request
    shipment_id = request.args.get('shipment_id')
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT shipment_number, status FROM shipments WHERE id=?', (shipment_id,))
    shipment = cursor.fetchone()
    conn.close()
    
    return render_template('distributors/update_delivery.html', shipment=shipment, shipment_id=shipment_id)

# Route: View shipment blockchain ledger
@distributors_bp.route('/shipment-blockchain/<int:shipment_id>')
def view_shipment_blockchain(shipment_id):
    if not check_distributor():
        return redirect('/login')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Get shipment info
    cursor.execute('SELECT shipment_number FROM shipments WHERE id=?', (shipment_id,))
    shipment = cursor.fetchone()
    
    if not shipment:
        conn.close()
        return redirect('/shipments')
    
    # Get blockchain records
    cursor.execute('''
        SELECT timestamp, location, user_role, farmer_name
        FROM supply_chain
        ORDER BY timestamp DESC
        LIMIT 50
    ''')
    blockchain_records = cursor.fetchall()
    
    conn.close()
    
    return render_template('distributors/shipment_blockchain.html',
                         shipment_number=shipment[0],
                         shipment_id=shipment_id,
                         blockchain_records=blockchain_records)

# API: Get shipments for dashboard
@distributors_bp.route('/api/shipments')
def api_get_shipments():
    if not check_distributor():
        return jsonify({"error": "Unauthorized"}), 403
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.id, s.shipment_number, s.status, s.expected_delivery_date
        FROM shipments s
        WHERE s.distributor_id=?
        ORDER BY s.shipment_date DESC
        LIMIT 10
    ''', (session['user_id'],))
    shipments = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'id': s[0],
        'shipment_number': s[1],
        'status': s[2],
        'expected_delivery_date': s[3]
    } for s in shipments])
