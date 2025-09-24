from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change for production

# Database connection (reused)
conn = sqlite3.connect('library.db', check_same_thread=False)
c = conn.cursor()

# Table creations and defaults (reused exactly)
c.execute('''CREATE TABLE IF NOT EXISTS users
             (name TEXT PRIMARY KEY, password TEXT, active INTEGER, admin INTEGER)''')
c.execute("INSERT OR IGNORE INTO users VALUES ('admin', 'adm', 1, 1)")
c.execute("INSERT OR IGNORE INTO users VALUES ('user', 'user', 1, 0)")

c.execute('''CREATE TABLE IF NOT EXISTS items
             (serial TEXT PRIMARY KEY, name TEXT, author TEXT, category TEXT, type TEXT, status TEXT, cost REAL, proc_date DATE)''')

c.execute('''CREATE TABLE IF NOT EXISTS members
             (id INTEGER PRIMARY KEY AUTOINCREMENT, first_name TEXT, last_name TEXT, contact TEXT, address TEXT, aadhar TEXT, 
              start_date DATE, end_date DATE, status TEXT, pending REAL)''')

c.execute('''CREATE TABLE IF NOT EXISTS issues
             (serial TEXT, member_id INTEGER, issue_date DATE, return_date DATE, actual_return DATE, fine_paid INTEGER, remarks TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS requests
             (member_id INTEGER, item_name TEXT, request_date DATE, fulfilled_date DATE)''')

conn.commit()

# Categories and prefixes (reused)
categories = ['Science', 'Economics', 'Fiction', 'Children', 'Personal Development']
prefixes = ['SC', 'EC', 'FC', 'CH', 'PD']

# Product details data (reused)
product_data = [
    ("SC(B/M)000001", "SC(B/M)000004", "Science"),
    ("EC(B/M)000001", "EC(B/M)000004", "Economics"),
    ("FC(B/M)000001", "FC(B/M)000004", "Fiction"),
    ("CH(B/M)000001", "CH(B/M)000004", "Children"),
    ("PD(B/M)000001", "PD(B/M)000004", "Personal Development"),
]

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        c.execute("SELECT * FROM users WHERE name=? AND password=? AND active=1", (username, password))
        user = c.fetchone()
        if user:
            session['user'] = username
            session['is_admin'] = bool(user[3])
            return redirect(url_for('home'))
        else:
            flash("Invalid credentials", "error")
    return render_template('login.html')

@app.route('/home')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    title = "Admin Home Page" if session['is_admin'] else "User Home Page"
    return render_template('home.html', title=title, is_admin=session['is_admin'], data=product_data)

@app.route('/maintenance')
def maintenance():
    if 'user' not in session or not session['is_admin']:
        return redirect(url_for('login'))
    return render_template('maintenance.html')

@app.route('/add_membership', methods=['GET', 'POST'])
def add_membership():
    if 'user' not in session or not session['is_admin']:
        return redirect(url_for('login'))
    start_date_default = datetime.now().strftime("%Y-%m-%d")
    if request.method == 'POST':
        first = request.form['first']
        last = request.form['last']
        contact = request.form['contact']
        address = request.form['address']
        aadhar = request.form['aadhar']
        start_date = request.form['start_date']
        duration = request.form['duration']
        if not all([first, last, contact, address, aadhar, start_date]):
            flash("All fields mandatory", "error")
            return render_template('add_membership.html', start_date_default=start_date_default)
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            if duration == "6 months":
                end = start + timedelta(days=180)
            elif duration == "1 year":
                end = start + timedelta(days=365)
            else:
                end = start + timedelta(days=730)
            c.execute("INSERT INTO members (first_name, last_name, contact, address, aadhar, start_date, end_date, status, pending) VALUES (?, ?, ?, ?, ?, ?, ?, 'Active', 0)",
                      (first, last, contact, address, aadhar, start_date, end.strftime("%Y-%m-%d")))
            conn.commit()
            flash("Transaction completed successfully", "success")
            return redirect(url_for('home'))
        except ValueError:
            flash("Invalid date format", "error")
    return render_template('add_membership.html', start_date_default=start_date_default)

@app.route('/update_membership', methods=['GET', 'POST'])
def update_membership():
    if 'user' not in session or not session['is_admin']:
        return redirect(url_for('login'))
    member = None
    if request.method == 'POST':
        if 'load' in request.form:
            mem_id = request.form['mem_id']
            c.execute("SELECT start_date, end_date FROM members WHERE id=?", (mem_id,))
            member = c.fetchone()
            if not member:
                flash("Invalid membership", "error")
            return render_template('update_membership.html', mem_id=mem_id, start_date=member[0] if member else '', end_date=member[1] if member else '')
        elif 'submit' in request.form:
            mem_id = request.form['mem_id']
            duration = request.form.get('duration', '6 months')
            remove = 'remove' in request.form
            c.execute("SELECT end_date FROM members WHERE id=?", (mem_id,))
            end_str = c.fetchone()
            if not end_str:
                flash("Invalid membership", "error")
                return render_template('update_membership.html')
            if remove:
                c.execute("UPDATE members SET status='Inactive' WHERE id=?", (mem_id,))
            else:
                end = datetime.strptime(end_str[0], "%Y-%m-%d")
                if duration == "6 months":
                    new_end = end + timedelta(days=180)
                elif duration == "1 year":
                    new_end = end + timedelta(days=365)
                else:
                    new_end = end + timedelta(days=730)
                c.execute("UPDATE members SET end_date=? WHERE id=?", (new_end.strftime("%Y-%m-%d"), mem_id))
            conn.commit()
            flash("Transaction completed successfully", "success")
            return redirect(url_for('home'))
    return render_template('update_membership.html', mem_id='', start_date='', end_date='')

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if 'user' not in session or not session['is_admin']:
        return redirect(url_for('login'))
    proc_date_default = datetime.now().strftime("%Y-%m-%d")
    if request.method == 'POST':
        typ = request.form['type']
        name = request.form['name']
        author = request.form['author']
        category = request.form['category']
        cost = request.form['cost']
        proc_date = request.form['proc_date']
        quantity = request.form['quantity']
        if not all([name, author, cost, proc_date, quantity]):
            flash("All fields mandatory", "error")
            return render_template('add_book.html', categories=categories, proc_date_default=proc_date_default)
        try:
            q = int(quantity)
            co = float(cost)
            prefix = prefixes[categories.index(category)]
            t = typ[0]
            like = prefix + '(' + t + ')' + '%'
            c.execute("SELECT MAX(CAST(SUBSTR(serial, 6, 6) AS INTEGER)) FROM items WHERE serial LIKE ?", (like,))
            max_num = c.fetchone()[0] or 0
            for i in range(q):
                num = max_num + i + 1
                serial = prefix + '(' + t + ')' + f"{num:06d}"
                c.execute("INSERT INTO items (serial, name, author, category, type, status, cost, proc_date) VALUES (?, ?, ?, ?, ?, 'Available', ?, ?)",
                          (serial, name, author, category, typ, co, proc_date))
            conn.commit()
            flash("Transaction completed successfully", "success")
            return redirect(url_for('home'))
        except ValueError:
            flash("Invalid quantity or cost", "error")
    return render_template('add_book.html', categories=categories, proc_date_default=proc_date_default)

@app.route('/update_book', methods=['GET', 'POST'])
def update_book():
    if 'user' not in session or not session['is_admin']:
        return redirect(url_for('login'))
    if request.method == 'POST':
        typ = request.form['type']
        name = request.form['name']
        serial = request.form['serial']
        status = request.form['status']
        date = request.form['date']
        if not serial:
            flash("Serial required", "error")
            return render_template('update_book.html')
        set_clause = "status = ?"
        values = [status]
        if date:
            set_clause += ", proc_date = ?"
            values.append(date)
        values.append(serial)
        c.execute(f"UPDATE items SET {set_clause} WHERE serial=?", values)
        conn.commit()
        flash("Transaction completed successfully", "success")
        return redirect(url_for('home'))
    return render_template('update_book.html')

@app.route('/user_management', methods=['GET', 'POST'])
def user_management():
    if 'user' not in session or not session['is_admin']:
        return redirect(url_for('login'))
    if request.method == 'POST':
        is_new = request.form['is_new']
        name = request.form['name']
        active = 'active' in request.form
        admin = 'admin' in request.form
        password = request.form['password']
        if not name:
            flash("Name mandatory", "error")
            return render_template('user_management.html')
        act = 1 if active else 0
        adm = 1 if admin else 0
        if is_new == "New":
            if not password:
                flash("Password required for new user", "error")
                return render_template('user_management.html')
            c.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (name, password, act, adm))
        else:
            set_clause = "active = ?, admin = ?"
            values = [act, adm]
            if password:
                set_clause += ", password = ?"
                values.append(password)
            values.append(name)
            c.execute(f"UPDATE users SET {set_clause} WHERE name=?", values)
        conn.commit()
        flash("Transaction completed successfully", "success")
        return redirect(url_for('home'))
    return render_template('user_management.html')

@app.route('/transactions')
def transactions():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('transactions.html')

@app.route('/book_available', methods=['GET', 'POST'])
def book_available():
    if 'user' not in session:
        return redirect(url_for('login'))
    results = []
    serial = request.args.get('serial')  # For issue from search
    if request.method == 'POST':
        name = request.form.get('name', '')
        author = request.form.get('author', '')
        where = ""
        values = []
        if name:
            where += "AND name LIKE ? "
            values.append('%' + name + '%')
        if author:
            where += "AND author LIKE ? "
            values.append('%' + author + '%')
        c.execute("SELECT name, author, serial, status FROM items WHERE 1 " + where, values)
        for row in c.fetchall():
            avail = "Y" if row[3] == "Available" else "N"
            results.append((row[0], row[1], row[2], avail))
    return render_template('book_available.html', results=results)

@app.route('/book_issue', methods=['GET', 'POST'])
def book_issue():
    if 'user' not in session:
        return redirect(url_for('login'))
    serial = request.args.get('serial')
    name_default = ''
    author_default = ''
    if serial:
        c.execute("SELECT name, author FROM items WHERE serial=?", (serial,))
        na = c.fetchone()
        if na:
            name_default = na[0]
            author_default = na[1]
    issue_date_default = datetime.now().strftime("%Y-%m-%d")
    return_date_default = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
    if request.method == 'POST':
        name = request.form['name']
        author = request.form['author']
        member = request.form['member']
        issue_date = request.form['issue_date']
        return_date = request.form['return_date']
        remarks = request.form['remarks']
        ser = serial
        if not ser:
            c.execute("SELECT serial FROM items WHERE name=? AND author=? AND status='Available' LIMIT 1", (name, author))
            s = c.fetchone()
            if not s:
                flash("No available item found", "error")
                return render_template('book_issue.html', name_default=name, author_default=author, issue_date_default=issue_date_default, return_date_default=return_date_default)
            ser = s[0]
        c.execute("SELECT * FROM members WHERE id=? AND status='Active'", (member,))
        if not c.fetchone():
            flash("Invalid active member", "error")
            return render_template('book_issue.html', name_default=name, author_default=author, issue_date_default=issue_date_default, return_date_default=return_date_default)
        c.execute("SELECT status FROM items WHERE serial=?", (ser,))
        if c.fetchone()[0] != "Available":
            flash("Not available", "error")
            return render_template('book_issue.html', name_default=name, author_default=author, issue_date_default=issue_date_default, return_date_default=return_date_default)
        c.execute("INSERT INTO issues (serial, member_id, issue_date, return_date, actual_return, fine_paid, remarks) VALUES (?, ?, ?, ?, NULL, 0, ?)",
                  (ser, member, issue_date, return_date, remarks))
        c.execute("UPDATE items SET status='Issued' WHERE serial=?", (ser,))
        conn.commit()
        flash("Transaction completed successfully", "success")
        return redirect(url_for('home'))
    return render_template('book_issue.html', name_default=name_default, author_default=author_default, issue_date_default=issue_date_default, return_date_default=return_date_default, serial_disabled=bool(serial))

@app.route('/return_book', methods=['GET', 'POST'])
def return_book():
    if 'user' not in session:
        return redirect(url_for('login'))
    issue_date = ''
    return_date_default = datetime.now().strftime("%Y-%m-%d")
    if request.method == 'POST':
        if 'load' in request.form:
            serial = request.form['serial']
            c.execute("SELECT issue_date FROM issues WHERE serial=? AND actual_return IS NULL", (serial,))
            idate = c.fetchone()
            if idate:
                issue_date = idate[0]
            else:
                flash("No active issue for this serial", "error")
            return render_template('return_book.html', issue_date=issue_date, return_date_default=return_date_default, serial=serial)
        elif 'submit' in request.form:
            serial = request.form['serial']
            actual = request.form['return_date']
            remarks = request.form['remarks']
            c.execute("UPDATE issues SET actual_return=?, remarks=? WHERE serial=? AND actual_return IS NULL", (actual, remarks, serial))
            if c.rowcount == 0:
                flash("No active issue", "error")
                return render_template('return_book.html', issue_date=issue_date, return_date_default=return_date_default)
            c.execute("UPDATE items SET status='Available' WHERE serial=?", (serial,))
            c.execute("SELECT return_date, member_id FROM issues WHERE serial=?", (serial,))
            ret, mid = c.fetchone()
            rdate = datetime.strptime(ret, "%Y-%m-%d")
            adate = datetime.strptime(actual, "%Y-%m-%d")
            days_over = max(0, (adate - rdate).days)
            fine = days_over * 1
            if fine > 0:
                c.execute("UPDATE members SET pending = pending + ? WHERE id=?", (fine, mid))
            conn.commit()
            flash("Transaction completed successfully", "success")
            return redirect(url_for('home'))
    return render_template('return_book.html', issue_date=issue_date, return_date_default=return_date_default, serial='')

@app.route('/pay_fine', methods=['GET', 'POST'])
def pay_fine():
    if 'user' not in session:
        return redirect(url_for('login'))
    issue_date = ''
    return_date = ''
    actual_return = ''
    fine_calc = '0'
    if request.method == 'POST':
        if 'load' in request.form:
            serial = request.form['serial']
            c.execute("SELECT issue_date, return_date, actual_return, member_id FROM issues WHERE serial=? AND fine_paid=0", (serial,))
            data = c.fetchone()
            if data:
                issue_date = data[0]
                return_date = data[1]
                actual_return = data[2] or ""
                if data[2]:
                    rdate = datetime.strptime(data[1], "%Y-%m-%d")
                    adate = datetime.strptime(data[2], "%Y-%m-%d")
                    days = max(0, (adate - rdate).days)
                    fine = days * 1
                    fine_calc = str(fine)
                else:
                    fine_calc = "0 (not returned)"
            else:
                flash("No pending fine for this serial", "error")
            return render_template('pay_fine.html', issue_date=issue_date, return_date=return_date, actual_return=actual_return, fine_calc=fine_calc, serial=serial)
        elif 'submit' in request.form:
            serial = request.form['serial']
            paid = 'paid' in request.form
            if paid:
                fine = float(request.form['fine_calc'])
                if fine > 0:
                    c.execute("SELECT member_id FROM issues WHERE serial=?", (serial,))
                    mid = c.fetchone()[0]
                    c.execute("UPDATE members SET pending = pending - ? WHERE id=?", (fine, mid))
                    c.execute("UPDATE issues SET fine_paid=1 WHERE serial=?", (serial,))
                    conn.commit()
                    flash("Transaction completed successfully", "success")
                    return redirect(url_for('home'))
                else:
                    flash("No fine to pay", "info")
            else:
                flash("No action taken", "info")
            return redirect(url_for('home'))
    return render_template('pay_fine.html', issue_date=issue_date, return_date=return_date, actual_return=actual_return, fine_calc=fine_calc, serial='')

@app.route('/reports')
def reports():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('reports.html')

@app.route('/master_list/<typ>')
def master_list(typ):
    if 'user' not in session:
        return redirect(url_for('login'))
    c.execute("SELECT serial, name, author, category, status, cost, proc_date FROM items WHERE type=?", (typ,))
    data = c.fetchall()
    title = f"Master List of {typ}s"
    columns = ["Serial No", "Name", "Author Name", "Category", "Status", "Cost", "Procurement Date"]
    return render_template('report_table.html', title=title, columns=columns, data=data)

@app.route('/members_list')
def members_list():
    if 'user' not in session:
        return redirect(url_for('login'))
    c.execute("SELECT id, first_name || ' ' || last_name, contact, address, aadhar, start_date, end_date, status, pending FROM members")
    data = c.fetchall()
    title = "Master List of Memberships"
    columns = ["Membership Id", "Name of Member", "Contact Number", "Contact Address", "Aadhar Card No", "Start Date", "End Date", "Status", "Amount Pending"]
    return render_template('report_table.html', title=title, columns=columns, data=data)

@app.route('/active_issues')
def active_issues():
    if 'user' not in session:
        return redirect(url_for('login'))
    c.execute("SELECT i.serial, it.name, i.member_id, i.issue_date, i.return_date FROM issues i JOIN items it ON i.serial = it.serial WHERE i.actual_return IS NULL")
    data = c.fetchall()
    title = "Active Issues"
    columns = ["Serial No Book/Movie", "Name of Book/Movie", "Membership Id", "Date of Issue", "Date of return"]
    return render_template('report_table.html', title=title, columns=columns, data=data)

@app.route('/overdue')
def overdue():
    if 'user' not in session:
        return redirect(url_for('login'))
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT i.serial, it.name, i.member_id, i.issue_date, i.return_date FROM issues i JOIN items it ON i.serial = it.serial WHERE i.actual_return IS NULL AND i.return_date < ?", (today,))
    data = []
    for row in c.fetchall():
        days = (datetime.today() - datetime.strptime(row[4], "%Y-%m-%d")).days
        fine = days * 1
        data.append(row + (fine,))
    title = "Overdue Returns"
    columns = ["Serial No Book", "Name of Book", "Membership Id", "Date of Issue", "Date of return", "Fine Calculations"]
    return render_template('report_table.html', title=title, columns=columns, data=data)

@app.route('/requests')
def requests():
    if 'user' not in session:
        return redirect(url_for('login'))
    c.execute("SELECT member_id, item_name, request_date, fulfilled_date FROM requests")
    data = c.fetchall()
    title = "Issue Requests"
    columns = ["Membership Id", "Name of Book/Movie", "Requested Date", "Request Fulfilled Date"]
    return render_template('report_table.html', title=title, columns=columns, data=data)

@app.route('/logout')
def logout():
    session.clear()
    flash("You have successfully logged out.", "success")
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)