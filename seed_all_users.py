import sqlite3
import random
import datetime

DATABASE = "database/organic_trace.db"

def seed_users():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('SELECT id, role FROM users')
    users = cursor.fetchall()
    
    roles = {'farmer': [], 'distributor': [], 'retailer': [], 'consumer': []}
    for u in users:
        role = u[1]
        if role in roles:
            roles[role].append(u[0])

    product_types = ['Vegetable', 'Fruit', 'Grain', 'Dairy']
    product_names = ['Organic Tomatoes', 'Fresh Apples', 'Wheat', 'Milk', 'Organic Carrots', 'Strawberries', 'Oats', 'Cheese', 'Potatoes', 'Lettuce']
    units = ['kg', 'liters', 'tons']

    print('Seeding specific data for existing users...')

    for f_id in roles['farmer']:
        for i in range(15):
            p_name = random.choice(product_names) + ' ' + str(random.randint(10000,99999))
            qty = round(random.uniform(50, 500), 2)
            date_added = (datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d')
            
            cursor.execute(
                'INSERT INTO products (product_name, product_type, farmer_id, status, certification_no, quantity, unit, date_added, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (p_name, random.choice(product_types), f_id, 'Active', f'CERT-{random.randint(10000,99999)}', qty, random.choice(units), date_added, 'High quality organic mock product.')
            )
            
            m_id = random.choice(roles['manufacturer']) if roles['manufacturer'] else None
            cursor.execute(
                'INSERT INTO entry_products (product_name, product_type, quantity, unit, certification_no, date_created, created_by, farmer_id, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (p_name, random.choice(product_types), qty/2, random.choice(units), f'CERT-{random.randint(10000,99999)}', date_added, f_id, f_id, m_id, 'Entry')
            )
            entry_id = cursor.lastrowid
            
            dist_id = random.choice(roles['distributor']) if roles['distributor'] else None
            cursor.execute(
                'INSERT INTO exit_products (product_name, product_type, quantity, unit, entry_product_id, certification_no, date_created, assigned_to_id, created_by, status, farmer_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (f'Processed Unit {random.randint(10000,99999)}', 'Processed', 50, 'kg', entry_id, f'CERT-{random.randint(10000,99999)}', date_added, dist_id, f_id, 'Assigned', f_id)
            )

    for m_id in roles['manufacturer']:
        for i in range(15):
            date_added = (datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d')
            cursor.execute(
                'INSERT INTO processing_batches (batch_number, batch_size, unit, acceptance_date, status) VALUES (?, ?, ?, ?, ?, ?)',
                (f'BATCH-{random.randint(100000,999999)}_{i}', m_id, random.randint(50, 200), 'kg', date_added, 'Completed')
            )
            pb_id = cursor.lastrowid
            
            cursor.execute(
                'INSERT INTO packaging_info (processing_batch_id, package_type, package_size, package_unit, number_of_packages, packaging_date, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (pb_id, 'Box', 10, 'kg', 10, date_added, m_id, 'Packaged')
            )
            pi_id = cursor.lastrowid
            
            for d_id in (roles.get('distributor') or []):
                if random.random() > 0.5:
                    cursor.execute(
                        'INSERT INTO shipments (shipment_number, packaging_info_id, distributor_id, shipment_date, expected_delivery_date, status) VALUES (?, ?, ?, ?, ?, ?, ?)',
                        (f'SHIP-{random.randint(100000,999999)}_{i}_{d_id}', pi_id, m_id, d_id, date_added, date_added, 'Delivered')
                    )

    for c_id in roles['consumer'] + roles['retailer']:
        for i in range(15):
            date_added = (datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d')
            cursor.execute(
                'INSERT INTO used_today (product_name, product_type, quantity, unit, exit_product_id, date_used, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (f'Consumed Mock Product {random.randint(10000,99999)}', 'Food', 5, 'kg', random.randint(1,10), date_added, c_id)
            )

    conn.commit()
    conn.close()
    print('Successfully ensured 15+ records for ALL active users across the database!')

if __name__ == '__main__':
    seed_users()
