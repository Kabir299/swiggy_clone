from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

def init_db():
    with sqlite3.connect("orders.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                          id INTEGER PRIMARY KEY AUTOINCREMENT, 
                          username TEXT UNIQUE, 
                          password TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
                          id INTEGER PRIMARY KEY AUTOINCREMENT, 
                          user_id INTEGER, 
                          name TEXT, contact TEXT, 
                          restaurant TEXT, food_item TEXT, 
                          quantity INTEGER, total_price REAL,
                          FOREIGN KEY (user_id) REFERENCES users(id))''')
        conn.commit()

init_db()

restaurants = {
    'Spicy Bites': {'description': "Authentic Indian flavors!", 'menu': {'Biryani': 12, 'Noodles': 10, 'Paneer Tikka': 8}},
    'Pasta Palace': {'description': "Delicious Italian dishes.", 'menu': {'Pasta Alfredo': 15, 'Garlic Bread': 5, 'Lasagna': 18}},
    'Burger Hub': {'description': "Juicy burgers & crispy fries!", 'menu': {'Cheeseburger': 8, 'Fries': 4, 'Milkshake': 6}}
}

def login_required(func):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))  # Redirects to login instead of welcome.html

@app.route('/home')
@login_required
def home():
    return render_template('index.html', restaurants=restaurants)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        with sqlite3.connect("orders.db") as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
                conn.commit()
                flash("Signup successful! Please log in.", "success")
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash("Username already exists!", "danger")
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect("orders.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, password FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['username'] = username
            flash("Login successful!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid username or password.", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))

@app.route('/order', methods=['GET', 'POST'])
@login_required
def order():
    if request.method == 'POST':
        name = request.form['name']
        contact = request.form['contact']
        restaurant_name = request.form['restaurant']
        food_item = request.form['food']
        quantity = int(request.form['quantity'])
        price_per_item = restaurants[restaurant_name]['menu'][food_item]
        total_price = price_per_item * quantity

        with sqlite3.connect("orders.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO orders (user_id, name, contact, restaurant, food_item, quantity, total_price) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                           (session['user_id'], name, contact, restaurant_name, food_item, quantity, total_price))
            conn.commit()

        return render_template('bill.html', name=name, contact=contact, restaurant=restaurant_name, food_item=food_item, quantity=quantity, total_price=total_price)

    return render_template('order.html', restaurants=restaurants)

@app.route('/history')
@login_required
def history():
    with sqlite3.connect("orders.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, contact, restaurant, food_item, quantity, total_price FROM orders WHERE user_id = ?", (session['user_id'],))
        orders = cursor.fetchall()
    return render_template('history.html', orders=orders)

if __name__ == '__main__':
    app.run(debug=True)