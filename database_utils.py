import sqlite3
import os

DATABASE_PATH = 'doctors.db'

def init_db():
    """Initialize the database and create the doctors, patients, and appointments tables if they don't exist."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Create doctors table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            specialty TEXT NOT NULL,
            location TEXT NOT NULL,
            experience INTEGER NOT NULL,
            photo TEXT
        )
    ''')

    # Create patients table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            patient_type TEXT NOT NULL,  -- 'Mother' or 'Child'
            risk_level TEXT NOT NULL,    -- 'Low Risk', 'Moderate Risk', 'High Risk'
            doctor_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (doctor_id) REFERENCES doctors (id)
        )
    ''')

    # Create appointments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY,
            patient_id INTEGER,
            doctor_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'Booked',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients (id),
            FOREIGN KEY (doctor_id) REFERENCES doctors (id)
        )
    ''')

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            mobile TEXT NOT NULL,
            google_id TEXT,
            name TEXT
        )
    ''')

    # Check if doctors data already exists
    cursor.execute('SELECT COUNT(*) FROM doctors')
    count = cursor.fetchone()[0]

    if count == 0:
        # Insert initial doctors data
        doctors_data = [
            (1, 'Dr. Sarah Johnson', 'Obstetrics & Gynecology', 'New York', 10, 'doctor1.jpg'),
            (2, 'Dr. Michael Chen', 'Pediatrics', 'Los Angeles', 8, 'doctor2.jpg'),
            (3, 'Dr. Emily Davis', 'Maternal-Fetal Medicine', 'Chicago', 12, 'doctor3.jpg'),
            (4, 'Dr. Robert Wilson', 'Neonatology', 'Houston', 15, 'doctor4.jpg'),
            (5, 'Dr. Lisa Brown', 'Family Medicine', 'Phoenix', 9, 'rupesh.jpg'),
        ]
        cursor.executemany('INSERT INTO doctors (id, name, specialty, location, experience, photo) VALUES (?, ?, ?, ?, ?, ?)', doctors_data)

    # Check if patients data already exists
    cursor.execute('SELECT COUNT(*) FROM patients')
    count = cursor.fetchone()[0]

    if count == 0:
        # Insert initial patients data
        patients_data = [
            (1, 'Sarah', 'Connor', 'Mother', 'High Risk', 1),
            (2, 'Baby', 'Doe', 'Child', 'Normal', 2),
            (3, 'Emily', 'Blunt', 'Mother', 'Moderate', 1),
            (4, 'John', 'Smith', 'Child', 'Normal', 2),
            (5, 'Anna', 'Davis', 'Mother', 'Low Risk', 3),
            (6, 'Michael', 'Johnson', 'Child', 'Normal', 4),
            (7, 'Lisa', 'Wilson', 'Mother', 'High Risk', 5),
            (8, 'David', 'Brown', 'Child', 'Moderate', 2),
            (9, 'Maria', 'Garcia', 'Mother', 'Low Risk', 1),
            (10, 'James', 'Miller', 'Child', 'Normal', 3),
            (11, 'Patricia', 'Taylor', 'Mother', 'Moderate', 4),
            (12, 'Robert', 'Anderson', 'Child', 'High Risk', 5),
            (13, 'Jennifer', 'Thomas', 'Mother', 'Low Risk', 1),
            (14, 'Christopher', 'Jackson', 'Child', 'Normal', 2),
            (15, 'Linda', 'White', 'Mother', 'High Risk', 3),
            (16, 'Daniel', 'Harris', 'Child', 'Moderate', 4),
            (17, 'Barbara', 'Martin', 'Mother', 'Low Risk', 5),
            (18, 'Matthew', 'Thompson', 'Child', 'Normal', 1),
        ]
        cursor.executemany('INSERT INTO patients (id, first_name, last_name, patient_type, risk_level, doctor_id) VALUES (?, ?, ?, ?, ?, ?)', patients_data)

    # Check if appointments data already exists
    cursor.execute('SELECT COUNT(*) FROM appointments')
    count = cursor.fetchone()[0]

    if count == 0:
        # Insert initial appointments data
        appointments_data = [
            (1, 1, 1, '2024-01-15', '10:00', 'Regular checkup', 'Completed'),
            (2, 2, 2, '2024-01-16', '14:30', 'Vaccination', 'Completed'),
            (3, 3, 1, '2024-01-17', '09:00', 'Follow-up', 'Completed'),
            (4, 4, 2, '2024-01-18', '11:15', 'Growth monitoring', 'Booked'),
            (5, 5, 3, '2024-01-19', '16:00', 'Prenatal care', 'Booked'),
            (6, 6, 4, '2024-01-20', '13:45', 'Newborn check', 'Scheduled'),
            (7, 7, 5, '2024-01-21', '08:30', 'High risk monitoring', 'Booked'),
        ]
        cursor.executemany('INSERT INTO appointments (id, patient_id, doctor_id, date, time, reason, status) VALUES (?, ?, ?, ?, ?, ?, ?)', appointments_data)

    conn.commit()
    conn.close()

def get_doctors(search_query=None, specialty=None, location=None):
    """Query doctors with optional filters."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    query = 'SELECT id, name, specialty, location, experience, photo FROM doctors WHERE 1=1'
    params = []

    if search_query:
        query += ' AND (name LIKE ? OR specialty LIKE ?)'
        params.extend([f'%{search_query}%', f'%{search_query}%'])

    if specialty:
        query += ' AND specialty = ?'
        params.append(specialty)

    if location:
        query += ' AND location = ?'
        params.append(location)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    # Convert to list of dicts
    doctors = []
    for row in rows:
        doctors.append({
            'id': row[0],
            'name': row[1],
            'specialty': row[2],
            'location': row[3],
            'experience': row[4],
            'photo': row[5]
        })

    return doctors

def get_all_specialties():
    """Get unique specialties."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT specialty FROM doctors')
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_all_locations():
    """Get unique locations."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT location FROM doctors')
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_doctor_by_id(doctor_id):
    """Get a single doctor by ID."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, specialty, location, experience, photo FROM doctors WHERE id = ?', (doctor_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            'id': row[0],
            'name': row[1],
            'specialty': row[2],
            'location': row[3],
            'experience': row[4],
            'photo': row[5]
        }
    return None

def get_patients(limit=10):
    """Get recent patients."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.id, p.first_name, p.last_name, p.patient_type, p.risk_level,
               d.name as doctor_name, p.created_at
        FROM patients p
        LEFT JOIN doctors d ON p.doctor_id = d.id
        ORDER BY p.created_at DESC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()

    patients = []
    for row in rows:
        patients.append({
            'id': row[0],
            'first_name': row[1],
            'last_name': row[2],
            'patient_type': row[3],
            'risk_level': row[4],
            'doctor_name': row[5] or 'Unassigned',
            'created_at': row[6]
        })
    return patients

def get_dashboard_stats():
    """Get dashboard statistics."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Total mothers
    cursor.execute("SELECT COUNT(*) FROM patients WHERE patient_type = 'Mother'")
    total_mothers = cursor.fetchone()[0]

    # High risk patients
    cursor.execute("SELECT COUNT(*) FROM patients WHERE risk_level = 'High Risk'")
    high_risk = cursor.fetchone()[0]

    # Monitored patients (assuming all patients are monitored)
    cursor.execute("SELECT COUNT(*) FROM patients")
    monitored = cursor.fetchone()[0]

    # Total reports (appointments)
    cursor.execute("SELECT COUNT(*) FROM appointments")
    total_reports = cursor.fetchone()[0]

    conn.close()

    return {
        'total_mothers': total_mothers,
        'high_risk': high_risk,
        'monitored': monitored,
        'total_reports': total_reports
    }

def get_risk_distribution():
    """Get risk level distribution for chart."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT risk_level, COUNT(*) as count
        FROM patients
        GROUP BY risk_level
    ''')
    rows = cursor.fetchall()
    conn.close()

    distribution = {'Low Risk': 0, 'Moderate Risk': 0, 'High Risk': 0}
    for row in rows:
        distribution[row[0]] = row[1]

    return distribution

def get_registration_trends():
    """Get patient registration trends over time (mock data for now)."""
    # For demo purposes, return mock data
    # In a real app, you'd aggregate by month from created_at
    return {
        'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        'data': [65, 78, 90, 85, 110, 120]
    }

def add_patient(first_name, last_name, patient_type, risk_level, doctor_id=None):
    """Add a new patient."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO patients (first_name, last_name, patient_type, risk_level, doctor_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (first_name, last_name, patient_type, risk_level, doctor_id))
    patient_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return patient_id

def add_appointment(patient_id, doctor_id, date, time, reason):
    """Add a new appointment."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO appointments (patient_id, doctor_id, date, time, reason)
        VALUES (?, ?, ?, ?, ?)
    ''', (patient_id, doctor_id, date, time, reason))
    appointment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return appointment_id

def add_user(username, password, mobile, google_id=None, name=None):
    """Add a new user."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (username, password, mobile, google_id, name)
        VALUES (?, ?, ?, ?, ?)
    ''', (username, password, mobile, google_id, name))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id

def get_user(username):
    """Get a user by username."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, password, mobile, google_id, name FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            'id': row[0],
            'username': row[1],
            'password': row[2],
            'mobile': row[3],
            'google_id': row[4],
            'name': row[5]
        }
    return None

def get_user_by_google_id(google_id):
    """Get a user by Google ID."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, password, mobile, google_id, name FROM users WHERE google_id = ?', (google_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            'id': row[0],
            'username': row[1],
            'password': row[2],
            'mobile': row[3],
            'google_id': row[4],
            'name': row[5]
        }
    return None

def update_user(username, mobile=None, google_id=None, name=None):
    """Update user information."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    updates = []
    params = []
    if mobile is not None:
        updates.append('mobile = ?')
        params.append(mobile)
    if google_id is not None:
        updates.append('google_id = ?')
        params.append(google_id)
    if name is not None:
        updates.append('name = ?')
        params.append(name)
    if updates:
        query = f'UPDATE users SET {", ".join(updates)} WHERE username = ?'
        params.append(username)
        cursor.execute(query, params)
        conn.commit()
    conn.close()
