from flask import Blueprint, render_template, request, redirect, session
import sqlite3
import hashlib

auth_bp = Blueprint('auth', __name__)
DATABASE = "database/organic_trace.db"

@auth_bp.route('/')
def home():
    return redirect('/login')

@auth_bp.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        role = request.form['role']
        status = 'approved' if role == 'admin' else 'pending'
        cursor.execute(
            "INSERT INTO users (name,email,password,role,status) VALUES (?,?,?,?,?)",
            (request.form['name'], request.form['email'], password, role, status)
        )
        conn.commit()
        conn.close()
        return redirect('/login')
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        account_type = request.form.get('account_type')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not account_type or not email or not password:
            return render_template('login.html', error='All fields are required')
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute("SELECT * FROM users WHERE email=? AND password=? AND role=?", 
                      (email, password_hash, account_type))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            if len(user) > 5 and user[5] != 'approved':
                return render_template('login.html', error=f'Account is {user[5]}. Please wait for admin approval.')
            
            session['user_id'] = user[0]
            session['name'] = user[1]
            session['role'] = user[4]
            return redirect('/dashboard')
        else:
            return render_template('login.html', error='Invalid email, password, or account type')
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect('/')