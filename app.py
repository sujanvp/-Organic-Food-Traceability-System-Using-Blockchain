from flask import Flask
from modules.auth import auth_bp
from modules.farmer import farmer_bp
from modules.distributors import distributors_bp
from modules.retailers import retailers_bp
from modules.consumers import consumers_bp
from modules.products import products_bp
from modules.profile import profile_bp
from modules.entry_products import entry_products_bp
from modules.exit_products import exit_products_bp
from modules.used_today import used_today_bp
from modules.track_food import track_food_bp
from modules.dashboard import dashboard_bp
from modules.admin import admin_bp
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

DATABASE = "database/organic_trace.db"

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT,
        status TEXT DEFAULT 'approved'
    )
    ''')
    
    # Create products table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT,
        product_type TEXT,
        farmer_id INTEGER,
        status TEXT,
        certification_no TEXT,
        quantity REAL,
        unit TEXT,
        date_added TEXT,
        description TEXT,
        FOREIGN KEY (farmer_id) REFERENCES users(id)
    )
    ''')
    
    # Create entry_products table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS entry_products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT,
        product_type TEXT,
        quantity REAL,
        unit TEXT,
        certification_no TEXT,
        date_created TEXT,
        created_by INTEGER,
        farmer_id INTEGER,
        status TEXT,
        description TEXT,
        FOREIGN KEY (created_by) REFERENCES users(id),
        FOREIGN KEY (farmer_id) REFERENCES users(id)
    )
    ''')
    
    # Create exit_products table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS exit_products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT,
        product_type TEXT,
        quantity REAL,
        unit TEXT,
        entry_product_id INTEGER,
        certification_no TEXT,
        date_created TEXT,
        assigned_to_id INTEGER,
        assigned_to_name TEXT,
        created_by INTEGER,
        status TEXT,
        farmer_id INTEGER,
        FOREIGN KEY (entry_product_id) REFERENCES entry_products(id),
        FOREIGN KEY (assigned_to_id) REFERENCES users(id),
        FOREIGN KEY (created_by) REFERENCES users(id),
        FOREIGN KEY (farmer_id) REFERENCES users(id)
    )
    ''')
    
    # Create used_today table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS used_today (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT,
        product_type TEXT,
        quantity REAL,
        unit TEXT,
        exit_product_id INTEGER,
        date_used TEXT,
        created_by INTEGER,
        source_user TEXT,
        FOREIGN KEY (exit_product_id) REFERENCES exit_products(id),
        FOREIGN KEY (created_by) REFERENCES users(id)
    )
    ''')
    
    # Create supply_chain table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS supply_chain (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        entry_product_id INTEGER,
        exit_product_id INTEGER,
        product_name TEXT,
        timestamp TEXT,
        location TEXT,
        user_role TEXT,
        farmer_name TEXT,
        FOREIGN KEY (product_id) REFERENCES products(id),
        FOREIGN KEY (entry_product_id) REFERENCES entry_products(id),
        FOREIGN KEY (exit_product_id) REFERENCES exit_products(id)
    )
    ''')
    
    # Create product_categories table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS product_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_name TEXT UNIQUE NOT NULL,
        description TEXT
    )
    ''')
    
    # Create certifications table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS certifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cert_name TEXT NOT NULL,
        cert_number TEXT UNIQUE NOT NULL,
        product_id INTEGER,
        user_id INTEGER,
        cert_date TEXT,
        expiry_date TEXT,
        issuing_authority TEXT,
        FOREIGN KEY (product_id) REFERENCES products(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    # Create quality_checks table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quality_checks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        entry_product_id INTEGER,
        checked_by INTEGER,
        check_date TEXT,
        quality_status TEXT,
        temperature REAL,
        humidity REAL,
        contamination_test TEXT,
        notes TEXT,
        FOREIGN KEY (product_id) REFERENCES products(id),
        FOREIGN KEY (entry_product_id) REFERENCES entry_products(id),
        FOREIGN KEY (checked_by) REFERENCES users(id)
    )
    ''')
    
    # Create inventory table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        user_id INTEGER,
        current_stock REAL,
        unit TEXT,
        last_updated TEXT,
        min_stock_level REAL,
        warehouse_location TEXT,
        FOREIGN KEY (product_id) REFERENCES products(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    # Create product_batch table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS product_batch (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_number TEXT UNIQUE NOT NULL,
        product_id INTEGER,
        created_by INTEGER,
        production_date TEXT,
        expiry_date TEXT,
        batch_size REAL,
        unit TEXT,
        batch_status TEXT,
        storage_location TEXT,
        FOREIGN KEY (product_id) REFERENCES products(id),
        FOREIGN KEY (created_by) REFERENCES users(id)
    )
    ''')
    
    # Create product_reviews table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS product_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        reviewed_by INTEGER,
        rating INTEGER,
        comments TEXT,
        review_date TEXT,
        FOREIGN KEY (product_id) REFERENCES products(id),
        FOREIGN KEY (reviewed_by) REFERENCES users(id)
    )
    ''')
    
    # Create organic_certifications table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS organic_certifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        cert_type TEXT,
        cert_number TEXT UNIQUE NOT NULL,
        issued_date TEXT,
        expiry_date TEXT,
        issuing_body TEXT,
        scope TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    # Create processing_batches table (Accept raw batch from farmer)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS processing_batches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_number TEXT UNIQUE NOT NULL,
        entry_product_id INTEGER,
        farmer_id INTEGER,
        manufacturer_id INTEGER,
        batch_size REAL,
        unit TEXT,
        acceptance_date TEXT,
        expected_completion_date TEXT,
        status TEXT,
        storage_location TEXT,
        notes TEXT,
        FOREIGN KEY (entry_product_id) REFERENCES entry_products(id),
        FOREIGN KEY (farmer_id) REFERENCES users(id),
        FOREIGN KEY (manufacturer_id) REFERENCES users(id)
    )
    ''')
    
    # Create processing_details table (Processing steps and details)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS processing_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        processing_batch_id INTEGER,
        process_step TEXT,
        process_description TEXT,
        process_date TEXT,
        process_time TEXT,
        temperature REAL,
        duration REAL,
        equipment_used TEXT,
        operator_name TEXT,
        status TEXT,
        FOREIGN KEY (processing_batch_id) REFERENCES processing_batches(id)
    )
    ''')
    
    # Create packaging_info table (Packaging details)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS packaging_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        processing_batch_id INTEGER,
        package_type TEXT,
        package_size REAL,
        package_unit TEXT,
        number_of_packages INTEGER,
        packaging_date TEXT,
        packaging_material TEXT,
        barcode_number TEXT,
        best_before_date TEXT,
        storage_instructions TEXT,
        manufacturer_id INTEGER,
        status TEXT,
        FOREIGN KEY (processing_batch_id) REFERENCES processing_batches(id),
        FOREIGN KEY (manufacturer_id) REFERENCES users(id)
    )
    ''')
    
    # Create quality_testing table (Quality testing reports)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quality_testing (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        processing_batch_id INTEGER,
        test_type TEXT,
        test_date TEXT,
        test_parameter TEXT,
        test_result TEXT,
        acceptance_criteria TEXT,
        status TEXT,
        tested_by INTEGER,
        remarks TEXT,
        FOREIGN KEY (processing_batch_id) REFERENCES processing_batches(id),
        FOREIGN KEY (tested_by) REFERENCES users(id)
    )
    ''')
    
    # Create shipments table (Accept shipment from farmer)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS shipments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shipment_number TEXT UNIQUE NOT NULL,
        exit_product_id INTEGER,
        farmer_id INTEGER,
        distributor_id INTEGER,
        shipment_date TEXT,
        expected_delivery_date TEXT,
        status TEXT,
        origin_location TEXT,
        destination_location TEXT,
        notes TEXT,
        FOREIGN KEY (exit_product_id) REFERENCES exit_products(id),
        FOREIGN KEY (farmer_id) REFERENCES users(id),
        FOREIGN KEY (distributor_id) REFERENCES users(id)
    )
    ''')
    
    # Create transport_details table (Add transport details)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transport_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shipment_id INTEGER,
        transport_mode TEXT,
        vehicle_number TEXT,
        transporter_name TEXT,
        driver_name TEXT,
        driver_contact TEXT,
        route TEXT,
        departure_time TEXT,
        estimated_arrival_time TEXT,
        actual_arrival_time TEXT,
        distance_km REAL,
        fuel_consumption REAL,
        notes TEXT,
        FOREIGN KEY (shipment_id) REFERENCES shipments(id)
    )
    ''')
    
    # Create storage_conditions table (Enter storage conditions)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS storage_conditions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shipment_id INTEGER,
        warehouse_location TEXT,
        storage_type TEXT,
        temperature REAL,
        humidity REAL,
        light_conditions TEXT,
        ventilation_status TEXT,
        security_measures TEXT,
        record_date TEXT,
        record_time TEXT,
        notes TEXT,
        FOREIGN KEY (shipment_id) REFERENCES shipments(id)
    )
    ''')
    
    # Create delivery_tracking table (Update delivery status)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS delivery_tracking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shipment_id INTEGER,
        status TEXT,
        status_update_date TEXT,
        status_update_time TEXT,
        location TEXT,
        recipient_name TEXT,
        recipient_contact TEXT,
        delivery_proof TEXT,
        signature_required BOOLEAN,
        signature_image TEXT,
        remarks TEXT,
        updated_by INTEGER,
        FOREIGN KEY (shipment_id) REFERENCES shipments(id),
        FOREIGN KEY (updated_by) REFERENCES users(id)
    )
    ''')
    
    conn.commit()
    conn.close()

def hash_sim(value):
    import hashlib
    return hashlib.md5(str(value).encode()).hexdigest()[:8]

def hash_sim_end(value):
    import hashlib
    return hashlib.md5(str(value).encode()).hexdigest()[-8:]

app.jinja_env.filters['hash_sim'] = hash_sim
app.jinja_env.filters['hash_sim_end'] = hash_sim_end
app.jinja_env.filters['zfill'] = lambda value, width: str(value).zfill(width)

init_db()

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(farmer_bp)
app.register_blueprint(distributors_bp)
app.register_blueprint(retailers_bp)
app.register_blueprint(consumers_bp)
app.register_blueprint(products_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(entry_products_bp)
app.register_blueprint(exit_products_bp)
app.register_blueprint(used_today_bp)
app.register_blueprint(track_food_bp)
app.register_blueprint(admin_bp)

if __name__ == "__main__":
    app.run(debug=True)