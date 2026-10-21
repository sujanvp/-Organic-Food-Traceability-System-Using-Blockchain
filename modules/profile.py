from flask import Blueprint, render_template, request, session, redirect, jsonify
import sqlite3
import hashlib
from datetime import datetime

profile_bp = Blueprint('profile', __name__)
DATABASE = "database/organic_trace.db"

@profile_bp.route('/profile')
def view_profile():
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, role FROM users WHERE id=?", (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return redirect('/login')
    
    return render_template('profile/view_profile.html', user=user)

@profile_bp.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    if request.method == 'POST':
        cursor.execute(
            "UPDATE users SET name=? WHERE id=?",
            (request.form['name'], session['user_id'])
        )
        conn.commit()
        conn.close()
        return redirect('/profile')
    
    cursor.execute("SELECT id, name, email, role FROM users WHERE id=?", (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    
    return render_template('profile/edit_profile.html', user=user)

@profile_bp.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        current_password = hashlib.sha256(request.form['current_password'].encode()).hexdigest()
        cursor.execute("SELECT password FROM users WHERE id=?", (session['user_id'],))
        user = cursor.fetchone()
        
        if not user or user[0] != current_password:
            conn.close()
            return render_template('profile/change_password.html', error='Current password is incorrect')
        
        if len(request.form['new_password']) < 6:
            conn.close()
            return render_template('profile/change_password.html', error='Password must be at least 6 characters')
        
        new_password = hashlib.sha256(request.form['new_password'].encode()).hexdigest()
        cursor.execute("UPDATE users SET password=? WHERE id=?", (new_password, session['user_id']))
        conn.commit()
        conn.close()
        
        return redirect('/profile')
    
    return render_template('profile/change_password.html')
