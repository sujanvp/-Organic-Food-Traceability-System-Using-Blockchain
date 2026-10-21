import sqlite3
import random
import datetime
import hashlib

DATABASE = "database/organic_trace.db"

def get_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()

def seed():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    roles = ['farmer', 'distributor', 'retailer', 'consumer']
    user_ids = {role: [] for role in roles}

    print("Adding Users...")
    for role in roles:
        for i in range(1, 6):
            name = f"{role.capitalize()} User {random.randint(1000, 9999)}"
            email = f"mock_{role}{i}_{random.randint(1000, 9999)}@test.com"
            cursor.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)", 
                           (name, email, get_hash('password123'), role))
            user_ids[role].append(cursor.lastrowid)

    product_types = ['Vegetable', 'Fruit', 'Grain', 'Dairy']
    product_names = ['Organic Tomatoes', 'Fresh Apples', 'Wheat', 'Milk', 'Organic Carrots', 'Strawberries', 'Oats', 'Cheese', 'Potatoes', 'Lettuce']
    units = ['kg', 'liters', 'tons']
    
    print("Adding Products...")
    product_ids = []
    farmer_ids = user_ids['farmer']
    for i in range(15):
        p_name = random.choice(product_names) + f" {random.randint(100,999)}"
        p_type = random.choice(product_types)
        f_id = random.choice(farmer_ids)
        qty = round(random.uniform(50, 500), 2)
        unit = random.choice(units)
        date_added = (datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d')
        
        cursor.execute('''INSERT INTO products (product_name, product_type, farmer_id, status, certification_no, quantity, unit, date_added, description)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (p_name, p_type, f_id, 'Active', f"CERT-{random.randint(1000,9999)}", qty, unit, date_added, "High quality organic mock product."))
        product_ids.append(cursor.lastrowid)

    print("Adding Entry Products...")
    entry_product_ids = []
    farmer_ids = user_ids['manufacturer']
    for i in range(15):
        p_name = random.choice(product_names) + f" Batch {random.randint(100,999)}"
        p_type = random.choice(product_types)
        f_id = random.choice(farmer_ids)
        qty = round(random.uniform(10, 200), 2)
        unit = random.choice(units)
        date_created = (datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 15))).strftime('%Y-%m-%d')
        m_id = random.choice(farmer_ids)
        
        cursor.execute('''INSERT INTO entry_products (product_name, product_type, quantity, unit, certification_no, date_created, created_by, farmer_id, status)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (p_name, p_type, qty, unit, f"CERT-{random.randint(1000,9999)}", date_created, f_id, f_id, m_id, 'Entry'))
        entry_id = cursor.lastrowid
        entry_product_ids.append(entry_id)

        # Supply chain log
        cursor.execute("INSERT INTO supply_chain (entry_product_id, product_name, timestamp, location, user_role) VALUES (?, ?, ?, ?, ?)",
                       (entry_id, p_name, date_created, "Farm Origin", "farmer"))

    print("Adding Exit Products...")
    exit_product_ids = []
    distributor_ids = user_ids['distributor']
    retailer_ids = user_ids['retailer']
    for i in range(15):
        entry_id = random.choice(entry_product_ids)
        f_id = random.choice(farmer_ids)
        assigned_id = random.choice(distributor_ids + retailer_ids)
        date_created = (datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 10))).strftime('%Y-%m-%d')
        
        cursor.execute('''INSERT INTO exit_products (product_name, product_type, quantity, unit, entry_product_id, certification_no, date_created, assigned_to_id, created_by, status, farmer_id)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (f"Processed Unit {random.randint(100,999)}", "Processed", 50, "kg", entry_id, f"CERT-{random.randint(1000,9999)}", date_created, assigned_id, f_id, 'Assigned', f_id))
        exit_id = cursor.lastrowid
        exit_product_ids.append(exit_id)

    print("Adding Used Today Logs...")
    consumer_ids = user_ids['consumer']
    for i in range(20):
        exit_id = random.choice(exit_product_ids)
        user_id = random.choice(retailer_ids + consumer_ids)
        date_used = (datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 5))).strftime('%Y-%m-%d')
        
        cursor.execute('''INSERT INTO used_today (product_name, product_type, quantity, unit, exit_product_id, date_used, created_by)
                          VALUES (?, ?, ?, ?, ?, ?, ?)''',
                       (f"Consumed Mock Product {random.randint(100,999)}", "Food", 5, "kg", exit_id, date_used, user_id))

    print("Adding Processing Batches...")
    processing_batch_ids = []
    for i in range(20):
        m_id = random.choice(farmer_ids)
        entry_id = random.choice(entry_product_ids)
        date_used = (datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 15))).strftime('%Y-%m-%d')
        status = random.choice(['Processing', 'Completed'])
        
        cursor.execute('''INSERT INTO processing_batches (batch_number, entry_product_id, batch_size, unit, acceptance_date, status)
                          VALUES (?, ?, ?, ?, ?, ?, ?)''',
                       (f"BATCH-{random.randint(10000,99999)}", entry_id, m_id, random.randint(50, 200), "kg", date_used, status))
        processing_batch_ids.append(cursor.lastrowid)

    print("Adding Packaging Infos...")
    packaging_info_ids = []
    for pb_id in processing_batch_ids:
        if random.random() > 0.2:
            m_id = random.choice(farmer_ids)
            cursor.execute('''INSERT INTO packaging_info (processing_batch_id, package_type, package_size, package_unit, number_of_packages, packaging_date, status)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                           (pb_id, 'Box', 10, 'kg', 10, datetime.datetime.now().strftime('%Y-%m-%d'), m_id, 'Packaged'))
            packaging_info_ids.append(cursor.lastrowid)

    print("Adding Shipments...")
    shipment_ids = []
    for pi_id in packaging_info_ids:
        d_id = random.choice(distributor_ids)
        m_id = random.choice(farmer_ids)
        status = random.choice(['Pending', 'In Transit', 'Delivered'])
        cursor.execute('''INSERT INTO shipments (shipment_number, packaging_info_id, distributor_id, shipment_date, expected_delivery_date, status)
                          VALUES (?, ?, ?, ?, ?, ?, ?)''',
                       (f"SHIP-{random.randint(10000,99999)}", pi_id, m_id, d_id, datetime.datetime.now().strftime('%Y-%m-%d'), datetime.datetime.now().strftime('%Y-%m-%d'), status))
        shipment_ids.append(cursor.lastrowid)

    conn.commit()
    conn.close()
    print("Database seeded effectively with 10-25 records per table!")

if __name__ == '__main__':
    seed()
