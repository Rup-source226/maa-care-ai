import sqlite3
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import pickle
import os
import openai
from openai import OpenAI
from functools import wraps
import stripe
from flask_dance.contrib.google import make_google_blueprint, google
from database_utils import add_appointment, init_db, get_doctors, get_all_specialties, get_all_locations, get_doctor_by_id, get_patients, get_dashboard_stats, get_risk_distribution, get_registration_trends, add_patient, add_user, get_user, get_user_by_google_id, update_user

app = Flask(__name__, template_folder='frontend/templates', static_folder='frontend/static')
app.secret_key = 'your-secret-key-here-change-in-production'  # Change this to a secure random key in production

# Google OAuth configuration
google_bp = make_google_blueprint(
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    scope=['profile', 'email']
)
app.register_blueprint(google_bp, url_prefix='/login')

# Stripe configuration (use test keys in production)
stripe.api_key = 'sk_test_your_stripe_secret_key_here'  # Replace with actual test key

# Initialize the database
init_db()

# Simple in-memory user store for demo purposes
users = {}  # {username: {'password': password, 'mobile': mobile}}

# In-memory data for appointments (for demo purposes)
appointments = []

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Load models
model_path = 'models/maternal_risk_model.pkl'
scaler_path = 'models/scaler.pkl'

if os.path.exists(model_path):
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
else:
    model = None
    scaler = None

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        mobile = request.form.get('mobile', '').strip()
        if not username or not password or not mobile:
            flash('Username, password, and mobile number are required.', 'error')
            return redirect(url_for('signup'))
        try:
            add_user(username, password, mobile)
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists.', 'error')
            return redirect(url_for('signup'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if not username or not password:
            flash('Username and password are required.', 'error')
            return redirect(url_for('login'))
        user = get_user(username)
        if not user or user['password'] != password:
            flash('Invalid username or password.', 'error')
            return redirect(url_for('login'))
        session['username'] = username
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/login/google/authorized')
def google_login():
    if not google.authorized:
        return redirect(url_for('google.login'))
    resp = google.get('/oauth2/v2/userinfo')
    if resp.ok:
        user_info = resp.json()
        email = user_info['email']
        google_id = user_info['id']
        name = user_info.get('name', email)

        # Check if user exists, if not create
        user = get_user_by_google_id(google_id)
        if not user:
            add_user(email, '', '', google_id, name)
        else:
            # Update name if not set
            if not user['name']:
                update_user(email, name=name)

        session['username'] = email
        flash('Logged in with Google successfully!', 'success')
        return redirect(url_for('index'))
    else:
        flash('Failed to login with Google.', 'error')
        return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@login_required
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    username = session['username']
    user_data = get_user(username)

    if request.method == 'POST':
        mobile = request.form.get('mobile', '').strip()
        if not mobile:
            flash('Mobile number is required.', 'error')
            return redirect(url_for('profile'))

        # Update user data
        update_user(username, mobile=mobile)
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html', user_data=user_data)

@login_required
@app.route('/maternal', methods=['GET', 'POST'])
def maternal():
    result = None
    error = None
    if request.method == 'POST':
        try:
            age_str = request.form.get('age', '').strip()
            bmi_str = request.form.get('bmi', '').strip()
            bp_str = request.form.get('bp', '').strip()
            hb_str = request.form.get('hb', '').strip()
            sugar_str = request.form.get('sugar', '').strip()

            if not all([age_str, bmi_str, bp_str, hb_str, sugar_str]):
                error = "All fields are required."
            else:
                age = float(age_str)
                bmi = float(bmi_str)
                # Handle bp as systolic/diastolic, take systolic
                if '/' in bp_str:
                    bp = float(bp_str.split('/')[0])
                else:
                    bp = float(bp_str)
                hb = float(hb_str)
                sugar = float(sugar_str)

                # Dummy prediction if model not loaded
                if model and scaler:
                    features = scaler.transform([[age, bmi, bp, hb, sugar]])
                    prediction = model.predict(features)[0]
                    result = 'High Risk' if prediction == 1 else 'Low Risk'
                else:
                    result = 'Low Risk' if age < 30 else 'High Risk'
        except ValueError as e:
            error = "Invalid input. Please enter numeric values."

    return render_template('maternal_risk.html', result=result, error=error)

@login_required
@app.route('/child', methods=['GET', 'POST'])
def child():
    status = None
    if request.method == 'POST':
        age = float(request.form['age'])
        height = float(request.form['height'])
        weight = float(request.form['weight'])
        gender = request.form['gender']

        # Dummy logic
        bmi = weight / ((height / 100) ** 2)
        if bmi < 18.5:
            status = 'Underweight'
        elif bmi < 25:
            status = 'Normal'
        else:
            status = 'Overweight'

    return render_template('child_growth.html', status=status)

@login_required
@app.route('/recommendations')
def recommendations():
    return render_template('recommendations.html')

@login_required
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@login_required
@app.route('/nutrition', methods=['GET', 'POST'])
def nutrition():
    plan = None
    if request.method == 'POST':
        user_type = request.form['user_type']
        age = float(request.form['age'])
        weight = float(request.form['weight'])
        height = float(request.form['height'])
        activity_level = request.form['activity_level']

        # Dummy diet plan generation
        if user_type == 'Mother':
            plan = f"Daily Calorie Intake: {weight * 30} kcal. Focus on iron-rich foods, folic acid, and calcium."
        else:
            plan = f"Child Diet Plan: Balanced meals with proteins, carbs, and veggies. Age-appropriate portions."

    return render_template('nutrition.html', plan=plan)

@login_required
@app.route('/reminders', methods=['GET', 'POST'])
def reminders():
    reminders_list = None
    if request.method == 'POST':
        user_type = request.form['user_type']
        age = float(request.form['age'])
        last_vaccine = request.form['last_vaccine']
        next_checkup = request.form['next_checkup']

        # Dummy reminders
        reminders_list = [
            f"Next vaccine due in {age + 1} months.",
            f"Checkup reminder: {next_checkup}",
            "Medication reminder: Prenatal vitamins daily."
        ]

    return render_template('reminders.html', reminders=reminders_list)



@login_required
@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

@login_required
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '')

        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        # System prompt for health-focused AI
        system_prompt = """You are a helpful AI health assistant specializing in maternal and child care. You provide accurate, evidence-based information about:

- Pregnancy and prenatal care
- Child development and growth
- Nutrition for mothers and children
- Common health concerns and preventive care
- General wellness advice

Important guidelines:
- Always emphasize consulting healthcare professionals for medical advice
- Provide general information, not personalized medical diagnoses
- Be supportive and encouraging
- Use clear, simple language
- If asked about serious medical conditions, recommend seeing a doctor

Remember: You are not a substitute for professional medical care."""

        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500,
            temperature=0.7
        )

        ai_response = response.choices[0].message.content.strip()

        return jsonify({'response': ai_response})

    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@login_required
@app.route('/appointments', methods=['GET', 'POST'])
def appointments_route():
    if request.method == 'POST':
        step = request.form.get('step', '1')

        if step == '1':  # Initial booking details
            doctor_id = int(request.form['doctor_id'])
            date = request.form['date']
            time = request.form['time']
            reason = request.form['reason']
            mobile = request.form['mobile']

            # Find the doctor
            doctor = get_doctor_by_id(doctor_id)
            if not doctor:
                flash('Doctor not found.', 'error')
                return redirect(url_for('appointments_route'))

            # Store in session for next steps
            session['appointment_data'] = {
                'doctor_id': doctor_id,
                'doctor': doctor,
                'date': date,
                'time': time,
                'reason': reason,
                'mobile': mobile
            }

            # Send OTP
            otp = '123456'  # Mock OTP
            otp_store[mobile] = otp
            print(f"Mock OTP sent to {mobile}: {otp}")

            return render_template('appointments.html', doctors=get_doctors(), appointments=[], step='otp', mobile=mobile)

        elif step == '2':  # OTP verification
            mobile = request.form['mobile']
            otp = request.form['otp']

            if mobile not in otp_store or otp_store[mobile] != otp:
                flash('Invalid OTP. Please try again.', 'error')
                return render_template('appointments.html', doctors=get_doctors(), appointments=[], step='otp', mobile=mobile)

            # OTP verified
            del otp_store[mobile]
            return render_template('appointments.html', doctors=get_doctors(), appointments=[], step='payment')

        elif step == '3':  # Payment and final booking
            if 'appointment_data' not in session:
                flash('Session expired. Please start over.', 'error')
                return redirect(url_for('appointments_route'))

            appointment_data = session['appointment_data']
            username = session['username']

            # Create a dummy patient for the appointment (in real app, patient would be selected/created)
            patient_id = add_patient('John', 'Doe', 'Mother', 'Low Risk', appointment_data['doctor_id'])

            # Create appointment in database
            appointment_id = add_appointment(
                patient_id=patient_id,
                doctor_id=appointment_data['doctor_id'],
                date=appointment_data['date'],
                time=appointment_data['time'],
                reason=appointment_data['reason']
            )

            # Clear session
            session.pop('appointment_data', None)

            flash('Appointment booked successfully!', 'success')
            return redirect(url_for('appointments_route'))

    # For demo, show all appointments (in real app, filter by user)
    # Since we don't have user-patient relationship, show recent appointments
    user_appointments = []  # Placeholder
    return render_template('appointments.html', doctors=get_doctors(), appointments=user_appointments, step='1')

@login_required
@app.route('/doctors', methods=['GET', 'POST'])
def doctors_route():
    search_query = request.args.get('search', '').lower()
    specialty_filter = request.args.get('specialty', '')
    location_filter = request.args.get('location', '')

    all_doctors = get_doctors()
    filtered_doctors = all_doctors

    if search_query:
        filtered_doctors = [d for d in filtered_doctors if search_query in d['name'].lower() or search_query in d['specialty'].lower()]

    if specialty_filter:
        filtered_doctors = [d for d in filtered_doctors if d['specialty'] == specialty_filter]

    if location_filter:
        filtered_doctors = [d for d in filtered_doctors if d['location'] == location_filter]

    specialties = list(set(d['specialty'] for d in all_doctors))
    locations = list(set(d['location'] for d in all_doctors))

    return render_template('doctors.html', doctors=filtered_doctors, specialties=specialties, locations=locations)

@login_required
@app.route('/doctor/<int:doctor_id>')
def doctor_profile(doctor_id):
    doctor = get_doctor_by_id(doctor_id)
    if not doctor:
        flash('Doctor not found.', 'error')
        return redirect(url_for('doctors_route'))
    return render_template('doctor_profile.html', doctor=doctor)

@login_required
@app.route('/video')
def video():
    return render_template('video.html')

# OTP store for demo purposes
otp_store = {}  # {mobile: otp}

@login_required
@app.route('/send_otp', methods=['POST'])
def send_otp():
    mobile = request.form.get('mobile', '').strip()
    if not mobile:
        return jsonify({'error': 'Mobile number required'}), 400

    # Mock OTP generation (in production, integrate with Twilio or similar)
    otp = '123456'  # Mock OTP for demo
    otp_store[mobile] = otp

    # For demo purposes, return the OTP in the response so user can see it
    # In production, remove this and send actual SMS
    return jsonify({'message': 'OTP sent successfully', 'otp': otp})

@login_required
@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    mobile = request.form.get('mobile', '').strip()
    otp = request.form.get('otp', '').strip()

    if not mobile or not otp:
        return jsonify({'error': 'Mobile and OTP required'}), 400

    if mobile not in otp_store or otp_store[mobile] != otp:
        return jsonify({'error': 'Invalid OTP'}), 400

    # OTP verified, remove from store
    del otp_store[mobile]
    return jsonify({'message': 'OTP verified successfully'})

# Dashboard API endpoints
@login_required
@app.route('/api/dashboard/stats')
def dashboard_stats():
    stats = get_dashboard_stats()
    return jsonify(stats)

@login_required
@app.route('/api/dashboard/patients')
def dashboard_patients():
    patients = get_patients(limit=10)
    return jsonify(patients)

@login_required
@app.route('/api/dashboard/risk-distribution')
def risk_distribution():
    distribution = get_risk_distribution()
    return jsonify(distribution)

@login_required
@app.route('/api/dashboard/registration-trends')
def registration_trends():
    trends = get_registration_trends()
    return jsonify(trends)

if __name__ == '__main__':
    app.run(debug=True)
