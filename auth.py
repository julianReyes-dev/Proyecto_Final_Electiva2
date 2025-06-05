from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from functools import wraps
from datetime import datetime
from models import db

auth_routes = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('auth.login', next=request.url))
        
        user = db.users.find_one({'_id': ObjectId(session['user_id'])})
        if not user or not user.get('is_admin'):
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

@auth_routes.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        is_admin = request.form.get('is_admin') == 'on'
        
        # Validation
        if not username or not password:
            flash('Username and password are required!', 'danger')
        elif password != confirm_password:
            flash('Passwords do not match!', 'danger')
        else:
            try:
                # Check if username already exists
                if db.users.find_one({'username': username}):
                    flash('Username already taken!', 'danger')
                else:
                    # Create new user
                    new_user = {
                        'username': username,
                        'password': generate_password_hash(password),
                        'is_admin': is_admin,
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    
                    db.users.insert_one(new_user)
                    flash('Registration successful! Please log in.', 'success')
                    return redirect(url_for('auth.login'))
            except Exception as e:
                flash(f'Error during registration: {str(e)}', 'danger')
    
    return render_template('auth/register.html')

@auth_routes.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if not username or not password:
            flash('Username and password are required!', 'danger')
        else:
            user = db.users.find_one({'username': username})
            if user and check_password_hash(user['password'], password):
                session['user_id'] = str(user['_id'])
                session['is_admin'] = user.get('is_admin', False)
                flash('Login successful!', 'success')
                
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard'))
            else:
                flash('Invalid username or password!', 'danger')
    
    return render_template('auth/login.html')

@auth_routes.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))