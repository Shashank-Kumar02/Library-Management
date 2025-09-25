# Library-Management
A simple, desktop-based Library Management System built with Python and Tkinter for the GUI, using SQLite as the backend database. This application allows admins to manage books/movies, memberships, and users, while both admins and users can handle transactions (issuing/returning items, paying fines) and view various reports.
<br/>
# Key Features
<br/>
Authentication: Separate logins for admins (full access) and users (read-only reports and transactions).
<br/>

# Maintenance (Admin Only):
<br/>
 Add/update memberships with durations (6 months, 1 year, 2 years).
 <br/>
 Add/update books/movies with auto-generated serial numbers (e.g., SC(B)000001 for Science books).
 <br/>
 User management (add/update active/admin status).
 <br/>
 
# Transactions:
<br/>
 Search for item availability by name/author.
<br/>
 Issue items to members (14-day default period).
<br/>
Return items with automatic fine calculation ($1/day overdue).
<br/>
Pay pending fines.
<br/>

# Reports:
<br/>
      Master lists for books, movies, and memberships.
<br/>
       Active issues, overdue returns (with fines), and pending requests.
</br/>

**Database Persistence:** All data stored in library.db (SQLite).
<br/>

**Validations:** Mandatory fields, error messages, and basic checks (e.g., item availability, active memberships).
<br/>

# Tech Stack
<br/>
Python 3.x
<br/>
HTML
<br/>
Tkinter (for GUI)
<br/>
SQLite (for database)
<br/>
datetime (for date handling)
</br>

# Installation
Ensure Python 3.6+ is installed (Tkinter and sqlite3 are built-in).
<br/>
Clone the repo: git clone https://github.com/yourusername/library-management-system.git
<br/>
Navigate to the directory: cd library-management-system
<br/>

# Usage
<br/>
Run the app: python app.py
<br/>

# Default logins:
<br/>
   Admin: Username admin, Password adm
   <br/>
   User: Username user, Password user
   <br/>
The app creates library.db automatically on first run.
