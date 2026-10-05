import os
from datetime import datetime, date
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from sqlalchemy import or_

from models import (
    db,
    Patient,
    Doctor,
    Appointment,
    Bill,
    generate_patient_id,
    generate_doctor_id,
    generate_appointment_id,
    generate_bill_id,
)

# ==========================================================
# APPLICATION SETUP
# ==========================================================
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SECRET_KEY'] = 'hospital-management-secret-key-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'database.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


# ==========================================================
# AUTHENTICATION DECORATORS
# ==========================================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def patient_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'patient' or not session.get('patient_id'):
            flash('Please log in with your Patient ID and Phone Number.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ==========================================================
# AUTHENTICATION ROUTES
# ==========================================================
@app.route('/')
def index():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    elif session.get('role') == 'patient':
        return redirect(url_for('patient_portal'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    if session.get('role') == 'patient':
        return redirect(url_for('patient_portal'))

    if request.method == 'POST':
        login_type = request.form.get('login_type', 'admin')

        # 1. PATIENT LOGIN (Patient ID + Registered Phone)
        if login_type == 'patient':
            patient_id_input = request.form.get('patient_id', '').strip()
            phone_input = request.form.get('phone', '').strip()

            clean_phone = ''.join(c for c in phone_input if c.isdigit())
            patient = Patient.query.filter(
                db.func.lower(Patient.patient_id) == patient_id_input.lower()
            ).first()

            if patient:
                db_phone = ''.join(c for c in patient.phone if c.isdigit())
                if clean_phone and (clean_phone == db_phone or clean_phone in db_phone or db_phone in clean_phone):
                    session.clear()
                    session['role'] = 'patient'
                    session['patient_id'] = patient.id
                    session['patient_code'] = patient.patient_id
                    session['patient_name'] = patient.name
                    flash(f'Welcome back, {patient.name}! You are logged into the Patient Portal.', 'success')
                    return redirect(url_for('patient_portal'))

            flash('Invalid Patient ID or Phone Number. Please check your credentials.', 'danger')

        # 2. ADMIN LOGIN (admin / admin123)
        else:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()

            if username == 'admin' and password == 'admin123':
                session.clear()
                session['logged_in'] = True
                session['role'] = 'admin'
                session['username'] = username
                flash('Login successful! Welcome to MEDITRACK.', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password. Please try again.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


# ==========================================================
# DASHBOARD ROUTE
# ==========================================================
@app.route('/dashboard')
@login_required
def dashboard():
    today_str = date.today().strftime('%Y-%m-%d')
    
    # Dashboard summary statistics
    total_patients = Patient.query.count()
    total_doctors = Doctor.query.count()
    today_appointments = Appointment.query.filter_by(appointment_date=today_str).count()
    total_bills = Bill.query.count()

    # Recent records for quick view
    recent_appointments = Appointment.query.order_by(Appointment.id.desc()).limit(5).all()
    recent_patients = Patient.query.order_by(Patient.id.desc()).limit(5).all()

    return render_template(
        'dashboard.html',
        total_patients=total_patients,
        total_doctors=total_doctors,
        today_appointments=today_appointments,
        total_bills=total_bills,
        recent_appointments=recent_appointments,
        recent_patients=recent_patients,
        today_str=today_str
    )


# ==========================================================
# PATIENTS MANAGEMENT
# ==========================================================
@app.route('/patients')
@login_required
def patients():
    search_query = request.args.get('q', '').strip()

    if search_query:
        # Search by patient_id, name, or phone
        patient_list = Patient.query.filter(
            or_(
                Patient.patient_id.ilike(f"%{search_query}%"),
                Patient.name.ilike(f"%{search_query}%"),
                Patient.phone.ilike(f"%{search_query}%")
            )
        ).order_by(Patient.id.desc()).all()
    else:
        patient_list = Patient.query.order_by(Patient.id.desc()).all()

    return render_template('patients.html', patients=patient_list, search_query=search_query)


@app.route('/patients/add', methods=['GET', 'POST'])
@login_required
def add_patient():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        age = request.form.get('age', '').strip()
        gender = request.form.get('gender', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        blood_group = request.form.get('blood_group', '').strip()
        disease = request.form.get('disease', '').strip()

        # Validations
        if not name or not age or not gender or not phone or not address or not blood_group or not disease:
            flash('All fields are required. Please fill out the entire form.', 'danger')
            return render_template('add_patient.html')

        try:
            age_int = int(age)
            if age_int <= 0 or age_int > 125:
                flash('Please enter a valid age between 1 and 125.', 'danger')
                return render_template('add_patient.html')
        except ValueError:
            flash('Age must be a valid whole number.', 'danger')
            return render_template('add_patient.html')

        # Simple phone validation (10 digits check)
        clean_phone = ''.join(c for c in phone if c.isdigit())
        if len(clean_phone) < 7 or len(clean_phone) > 15:
            flash('Please enter a valid phone number (7 to 15 digits).', 'danger')
            return render_template('add_patient.html')

        new_patient_id = generate_patient_id()
        new_patient = Patient(
            patient_id=new_patient_id,
            name=name,
            age=age_int,
            gender=gender,
            phone=phone,
            address=address,
            blood_group=blood_group,
            disease=disease
        )

        db.session.add(new_patient)
        db.session.commit()

        flash(f'Patient {name} ({new_patient_id}) added successfully!', 'success')
        return redirect(url_for('patients'))

    return render_template('add_patient.html')


@app.route('/patients/<int:id>')
@login_required
def patient_details(id):
    patient = db.get_or_404(Patient, id)
    return render_template('patient_details.html', patient=patient)


@app.route('/patients/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_patient(id):
    patient = db.get_or_404(Patient, id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        age = request.form.get('age', '').strip()
        gender = request.form.get('gender', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        blood_group = request.form.get('blood_group', '').strip()
        disease = request.form.get('disease', '').strip()

        # Validations
        if not name or not age or not gender or not phone or not address or not blood_group or not disease:
            flash('All fields are required.', 'danger')
            return render_template('edit_patient.html', patient=patient)

        try:
            age_int = int(age)
            if age_int <= 0 or age_int > 125:
                flash('Please enter a valid age between 1 and 125.', 'danger')
                return render_template('edit_patient.html', patient=patient)
        except ValueError:
            flash('Age must be a valid whole number.', 'danger')
            return render_template('edit_patient.html', patient=patient)

        patient.name = name
        patient.age = age_int
        patient.gender = gender
        patient.phone = phone
        patient.address = address
        patient.blood_group = blood_group
        patient.disease = disease

        db.session.commit()
        flash(f'Patient {patient.name} updated successfully!', 'success')
        return redirect(url_for('patient_details', id=patient.id))

    return render_template('edit_patient.html', patient=patient)


@app.route('/patients/delete/<int:id>', methods=['POST'])
@login_required
def delete_patient(id):
    patient = db.get_or_404(Patient, id)
    patient_name = patient.name
    db.session.delete(patient)
    db.session.commit()
    flash(f'Patient {patient_name} and related records have been deleted.', 'info')
    return redirect(url_for('patients'))


# ==========================================================
# DOCTORS MANAGEMENT
# ==========================================================
@app.route('/doctors')
@login_required
def doctors():
    search_query = request.args.get('q', '').strip()

    if search_query:
        # Search by Doctor name or speciality
        doctor_list = Doctor.query.filter(
            or_(
                Doctor.name.ilike(f"%{search_query}%"),
                Doctor.speciality.ilike(f"%{search_query}%")
            )
        ).order_by(Doctor.id.asc()).all()
    else:
        doctor_list = Doctor.query.order_by(Doctor.id.asc()).all()

    return render_template('doctors.html', doctors=doctor_list, search_query=search_query)


@app.route('/doctors/add', methods=['GET', 'POST'])
@login_required
def add_doctor():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        speciality = request.form.get('speciality', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        consultation_fee = request.form.get('consultation_fee', '').strip()
        available_days = request.form.get('available_days', '').strip()

        if not name or not speciality or not phone or not email or not consultation_fee or not available_days:
            flash('All fields are required. Please complete the form.', 'danger')
            return render_template('add_doctor.html')

        try:
            fee_float = float(consultation_fee)
            if fee_float < 0:
                flash('Consultation fee cannot be negative.', 'danger')
                return render_template('add_doctor.html')
        except ValueError:
            flash('Consultation fee must be a valid number.', 'danger')
            return render_template('add_doctor.html')

        new_doc_id = generate_doctor_id()
        new_doctor = Doctor(
            doctor_id=new_doc_id,
            name=name if name.startswith('Dr.') else f"Dr. {name}",
            speciality=speciality,
            phone=phone,
            email=email,
            consultation_fee=fee_float,
            available_days=available_days
        )

        db.session.add(new_doctor)
        db.session.commit()

        flash(f'Doctor {new_doctor.name} ({new_doc_id}) added successfully!', 'success')
        return redirect(url_for('doctors'))

    return render_template('add_doctor.html')


@app.route('/doctors/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_doctor(id):
    doctor = db.get_or_404(Doctor, id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        speciality = request.form.get('speciality', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        consultation_fee = request.form.get('consultation_fee', '').strip()
        available_days = request.form.get('available_days', '').strip()

        if not name or not speciality or not phone or not email or not consultation_fee or not available_days:
            flash('All fields are required.', 'danger')
            return render_template('edit_doctor.html', doctor=doctor)

        try:
            fee_float = float(consultation_fee)
            if fee_float < 0:
                flash('Consultation fee cannot be negative.', 'danger')
                return render_template('edit_doctor.html', doctor=doctor)
        except ValueError:
            flash('Consultation fee must be a valid number.', 'danger')
            return render_template('edit_doctor.html', doctor=doctor)

        doctor.name = name if name.startswith('Dr.') else f"Dr. {name}"
        doctor.speciality = speciality
        doctor.phone = phone
        doctor.email = email
        doctor.consultation_fee = fee_float
        doctor.available_days = available_days

        db.session.commit()
        flash(f'Doctor {doctor.name} updated successfully!', 'success')
        return redirect(url_for('doctors'))

    return render_template('edit_doctor.html', doctor=doctor)


@app.route('/doctors/delete/<int:id>', methods=['POST'])
@login_required
def delete_doctor(id):
    doctor = db.get_or_404(Doctor, id)
    doc_name = doctor.name
    db.session.delete(doctor)
    db.session.commit()
    flash(f'Doctor {doc_name} removed successfully.', 'info')
    return redirect(url_for('doctors'))


# ==========================================================
# APPOINTMENTS MANAGEMENT
# ==========================================================
@app.route('/appointments')
@login_required
def appointments():
    search_query = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = Appointment.query.join(Patient).join(Doctor)

    if search_query:
        # Search by patient name, doctor name, appointment date, reason, or appointment ID
        query = query.filter(
            or_(
                Patient.name.ilike(f"%{search_query}%"),
                Doctor.name.ilike(f"%{search_query}%"),
                Appointment.appointment_date.ilike(f"%{search_query}%"),
                Appointment.reason.ilike(f"%{search_query}%"),
                Appointment.appointment_id.ilike(f"%{search_query}%")
            )
        )

    if status_filter and status_filter in ['Scheduled', 'Completed', 'Cancelled']:
        query = query.filter(Appointment.status == status_filter)

    appointment_list = query.order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc()).all()
    return render_template('appointments.html', appointments=appointment_list, search_query=search_query, current_status=status_filter)


@app.route('/appointments/book', methods=['GET', 'POST'])
@login_required
def book_appointment():
    patients = Patient.query.order_by(Patient.name.asc()).all()
    doctors = Doctor.query.order_by(Doctor.name.asc()).all()

    # Pre-selection if query param provided
    selected_patient_id = request.args.get('patient_id', type=int)
    selected_doctor_id = request.args.get('doctor_id', type=int)

    if request.method == 'POST':
        patient_id = request.form.get('patient_id', type=int)
        doctor_id = request.form.get('doctor_id', type=int)
        appointment_date = request.form.get('appointment_date', '').strip()
        appointment_time = request.form.get('appointment_time', '').strip()
        reason = request.form.get('reason', '').strip()

        if not patient_id or not doctor_id or not appointment_date or not appointment_time or not reason:
            flash('All appointment fields are required.', 'danger')
            return render_template('book_appointment.html', patients=patients, doctors=doctors, selected_patient_id=patient_id, selected_doctor_id=doctor_id)

        # Validate Doctor exists
        doctor = db.session.get(Doctor, doctor_id)
        if not doctor:
            flash('Selected doctor not found.', 'danger')
            return render_template('book_appointment.html', patients=patients, doctors=doctors)

        # PREVENT DUPLICATE DOCTOR APPOINTMENT
        # Same doctor cannot be booked for the exact same date and time unless the existing appointment was cancelled
        conflict = Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == appointment_date,
            Appointment.appointment_time == appointment_time,
            Appointment.status != 'Cancelled'
        ).first()

        if conflict:
            flash(f'Slot conflict: {doctor.name} is already booked on {appointment_date} at {appointment_time}. Please select another time or date.', 'danger')
            return render_template('book_appointment.html', patients=patients, doctors=doctors, selected_patient_id=patient_id, selected_doctor_id=doctor_id)

        new_apt_id = generate_appointment_id()
        new_appointment = Appointment(
            appointment_id=new_apt_id,
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            reason=reason,
            status='Scheduled'
        )

        db.session.add(new_appointment)
        db.session.commit()

        flash(f'Appointment booked successfully ({new_apt_id})!', 'success')
        return redirect(url_for('appointments'))

    return render_template('book_appointment.html', patients=patients, doctors=doctors, selected_patient_id=selected_patient_id, selected_doctor_id=selected_doctor_id)


@app.route('/appointments/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_appointment(id):
    appointment = db.get_or_404(Appointment, id)
    patients = Patient.query.order_by(Patient.name.asc()).all()
    doctors = Doctor.query.order_by(Doctor.name.asc()).all()

    if request.method == 'POST':
        patient_id = request.form.get('patient_id', type=int)
        doctor_id = request.form.get('doctor_id', type=int)
        appointment_date = request.form.get('appointment_date', '').strip()
        appointment_time = request.form.get('appointment_time', '').strip()
        reason = request.form.get('reason', '').strip()
        status = request.form.get('status', '').strip()

        if not patient_id or not doctor_id or not appointment_date or not appointment_time or not reason or not status:
            flash('All fields are required.', 'danger')
            return render_template('edit_appointment.html', appointment=appointment, patients=patients, doctors=doctors)

        # Check for conflict excluding this current appointment
        conflict = Appointment.query.filter(
            Appointment.id != appointment.id,
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == appointment_date,
            Appointment.appointment_time == appointment_time,
            Appointment.status != 'Cancelled'
        ).first()

        if conflict:
            flash('Slot conflict: Doctor is already booked for this date and time slot.', 'danger')
            return render_template('edit_appointment.html', appointment=appointment, patients=patients, doctors=doctors)

        appointment.patient_id = patient_id
        appointment.doctor_id = doctor_id
        appointment.appointment_date = appointment_date
        appointment.appointment_time = appointment_time
        appointment.reason = reason
        appointment.status = status

        db.session.commit()
        flash('Appointment updated successfully!', 'success')
        return redirect(url_for('appointments'))

    return render_template('edit_appointment.html', appointment=appointment, patients=patients, doctors=doctors)


@app.route('/appointments/status/<int:id>/<new_status>', methods=['POST'])
@login_required
def update_appointment_status(id, new_status):
    appointment = db.get_or_404(Appointment, id)
    if new_status in ['Scheduled', 'Completed', 'Cancelled']:
        appointment.status = new_status
        db.session.commit()
        flash(f'Appointment status updated to {new_status}.', 'success')
    else:
        flash('Invalid status update.', 'danger')
    return redirect(url_for('appointments'))


@app.route('/appointments/delete/<int:id>', methods=['POST'])
@login_required
def delete_appointment(id):
    appointment = db.get_or_404(Appointment, id)
    db.session.delete(appointment)
    db.session.commit()
    flash('Appointment deleted.', 'info')
    return redirect(url_for('appointments'))


# ==========================================================
# BILL GENERATOR & BILLING
# ==========================================================
@app.route('/bills')
@login_required
def bills():
    search_query = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = Bill.query.join(Patient)

    if search_query:
        query = query.filter(
            or_(
                Bill.bill_id.ilike(f"%{search_query}%"),
                Patient.name.ilike(f"%{search_query}%"),
                Patient.patient_id.ilike(f"%{search_query}%")
            )
        )

    if status_filter and status_filter in ['Paid', 'Pending']:
        query = query.filter(Bill.payment_status == status_filter)

    bill_list = query.order_by(Bill.id.desc()).all()
    return render_template('bills.html', bills=bill_list, search_query=search_query, current_status=status_filter)


@app.route('/bills/generate', methods=['GET', 'POST'])
@login_required
def generate_bill():
    patients = Patient.query.order_by(Patient.name.asc()).all()
    doctors = Doctor.query.order_by(Doctor.name.asc()).all()

    selected_patient_id = request.args.get('patient_id', type=int)

    if request.method == 'POST':
        patient_id = request.form.get('patient_id', type=int)
        doctor_id = request.form.get('doctor_id', type=int)
        
        try:
            consultation_fee = float(request.form.get('consultation_fee', 0) or 0)
            medicine_charges = float(request.form.get('medicine_charges', 0) or 0)
            test_charges = float(request.form.get('test_charges', 0) or 0)
            other_charges = float(request.form.get('other_charges', 0) or 0)
            discount = float(request.form.get('discount', 0) or 0)
        except ValueError:
            flash('All monetary charges must be valid numbers.', 'danger')
            return render_template('generate_bill.html', patients=patients, doctors=doctors, selected_patient_id=patient_id)

        payment_status = request.form.get('payment_status', 'Paid').strip()
        if payment_status not in ['Paid', 'Pending']:
            payment_status = 'Paid'

        # Check non-negative
        if any(val < 0 for val in [consultation_fee, medicine_charges, test_charges, other_charges, discount]):
            flash('Charges and discount values cannot be negative numbers.', 'danger')
            return render_template('generate_bill.html', patients=patients, doctors=doctors, selected_patient_id=patient_id)

        # Automatic calculation formula:
        # Total = Consultation + Medicine + Test + Other - Discount
        subtotal = consultation_fee + medicine_charges + test_charges + other_charges
        total_amount = subtotal - discount

        if total_amount < 0:
            flash('Discount cannot be greater than total charges. Total amount cannot be negative.', 'danger')
            return render_template('generate_bill.html', patients=patients, doctors=doctors, selected_patient_id=patient_id)

        if not patient_id:
            flash('Please select a patient.', 'danger')
            return render_template('generate_bill.html', patients=patients, doctors=doctors)

        new_bill_id = generate_bill_id()
        new_bill = Bill(
            bill_id=new_bill_id,
            patient_id=patient_id,
            doctor_id=doctor_id if doctor_id else None,
            consultation_fee=consultation_fee,
            medicine_charges=medicine_charges,
            test_charges=test_charges,
            other_charges=other_charges,
            discount=discount,
            total_amount=round(total_amount, 2),
            payment_status=payment_status,
            bill_date=datetime.now()
        )

        db.session.add(new_bill)
        db.session.commit()

        flash(f'Bill {new_bill_id} generated successfully!', 'success')
        return redirect(url_for('bill_details', id=new_bill.id))

    return render_template('generate_bill.html', patients=patients, doctors=doctors, selected_patient_id=selected_patient_id)


@app.route('/bills/<int:id>')
def bill_details(id):
    bill = db.get_or_404(Bill, id)
    # Check authorization: Admin can view any bill; Patient can only view their own bill
    if session.get('logged_in'):
        return render_template('bill_details.html', bill=bill)
    elif session.get('role') == 'patient' and session.get('patient_id') == bill.patient_id:
        return render_template('bill_details.html', bill=bill)
    else:
        flash('Please log in to view this bill.', 'warning')
        return redirect(url_for('login'))


@app.route('/bills/status/<int:id>/<new_status>', methods=['POST'])
@login_required
def update_bill_status(id, new_status):
    bill = db.get_or_404(Bill, id)
    if new_status in ['Paid', 'Pending']:
        bill.payment_status = new_status
        db.session.commit()
        flash(f'Bill status updated to {new_status}.', 'success')
    return redirect(url_for('bill_details', id=bill.id))


@app.route('/bills/delete/<int:id>', methods=['POST'])
@login_required
def delete_bill(id):
    bill = db.get_or_404(Bill, id)
    db.session.delete(bill)
    db.session.commit()
    flash('Bill deleted successfully.', 'info')
    return redirect(url_for('bills'))


# ==========================================================
# PATIENT PORTAL ROUTES
# ==========================================================
@app.route('/patient-portal')
@patient_login_required
def patient_portal():
    patient = db.get_or_404(Patient, session['patient_id'])
    return render_template('patient_portal.html', patient=patient)


@app.route('/patient/book-appointment', methods=['GET', 'POST'])
@patient_login_required
def patient_book_appointment():
    patient = db.get_or_404(Patient, session['patient_id'])
    doctors = Doctor.query.order_by(Doctor.name.asc()).all()

    if request.method == 'POST':
        doctor_id = request.form.get('doctor_id', type=int)
        appointment_date = request.form.get('appointment_date', '').strip()
        appointment_time = request.form.get('appointment_time', '').strip()
        reason = request.form.get('reason', '').strip()

        if not doctor_id or not appointment_date or not appointment_time or not reason:
            flash('All appointment fields are required.', 'danger')
            return render_template('patient_book_appointment.html', patient=patient, doctors=doctors)

        doctor = db.session.get(Doctor, doctor_id)
        if not doctor:
            flash('Selected doctor not found.', 'danger')
            return render_template('patient_book_appointment.html', patient=patient, doctors=doctors)

        # Duplicate conflict check
        conflict = Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == appointment_date,
            Appointment.appointment_time == appointment_time,
            Appointment.status != 'Cancelled'
        ).first()

        if conflict:
            flash(f'Slot conflict: {doctor.name} is already booked on {appointment_date} at {appointment_time}. Please choose another time or date.', 'danger')
            return render_template('patient_book_appointment.html', patient=patient, doctors=doctors)

        new_apt_id = generate_appointment_id()
        new_appointment = Appointment(
            appointment_id=new_apt_id,
            patient_id=patient.id,
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            reason=reason,
            status='Scheduled'
        )
        db.session.add(new_appointment)
        db.session.commit()

        flash(f'Appointment booked successfully ({new_apt_id}) with {doctor.name}!', 'success')
        return redirect(url_for('patient_portal'))

    return render_template('patient_book_appointment.html', patient=patient, doctors=doctors)


# ==========================================================
# DATABASE SEEDING FOR DEMO / FIRST-RUN
# ==========================================================
def seed_initial_data():
    """Seeds sample data so the system works immediately on first run."""
    if Doctor.query.first() is not None:
        return  # Already seeded

    print("--- Seeding initial hospital data ---")

    # 1. Doctors as requested in the specification
    sample_doctors = [
        Doctor(
            doctor_id="DOC-101",
            name="Dr. Rahul Sharma",
            speciality="Cardiologist",
            phone="9876543210",
            email="rahul.sharma@meditrack.com",
            consultation_fee=800.0,
            available_days="Monday to Friday"
        ),
        Doctor(
            doctor_id="DOC-102",
            name="Dr. Priya Singh",
            speciality="Dermatologist",
            phone="9876543211",
            email="priya.singh@meditrack.com",
            consultation_fee=600.0,
            available_days="Mon, Wed, Fri"
        ),
        Doctor(
            doctor_id="DOC-103",
            name="Dr. Amit Verma",
            speciality="General Physician",
            phone="9876543212",
            email="amit.verma@meditrack.com",
            consultation_fee=500.0,
            available_days="Monday to Saturday"
        ),
        Doctor(
            doctor_id="DOC-104",
            name="Dr. Neha Gupta",
            speciality="Pediatrician",
            phone="9876543213",
            email="neha.gupta@meditrack.com",
            consultation_fee=700.0,
            available_days="Tue, Thu, Sat"
        ),
        Doctor(
            doctor_id="DOC-105",
            name="Dr. Vikram Sethi",
            speciality="Orthopedic",
            phone="9876543214",
            email="vikram.sethi@meditrack.com",
            consultation_fee=750.0,
            available_days="Mon, Tue, Thu"
        ),
    ]
    db.session.add_all(sample_doctors)
    db.session.commit()

    # 2. Patients
    sample_patients = [
        Patient(
            patient_id="PAT-1001",
            name="Rajesh Kumar",
            age=45,
            gender="Male",
            phone="9811223344",
            address="123 MG Road, New Delhi",
            blood_group="B+",
            disease="Hypertension & Chest Discomfort"
        ),
        Patient(
            patient_id="PAT-1002",
            name="Sunita Sharma",
            age=34,
            gender="Female",
            phone="9822334455",
            address="45 Park Street, Kolkata",
            blood_group="O+",
            disease="Skin Allergy & Chronic Rash"
        ),
        Patient(
            patient_id="PAT-1003",
            name="Mohammed Ali",
            age=28,
            gender="Male",
            phone="9833445566",
            address="78 Lake View, Bengaluru",
            blood_group="A+",
            disease="High Fever & Persistent Cough"
        ),
        Patient(
            patient_id="PAT-1004",
            name="Anita Patel",
            age=52,
            gender="Female",
            phone="9844556677",
            address="12 Ring Road, Ahmedabad",
            blood_group="AB+",
            disease="Knee Joint Pain & Arthritis"
        ),
    ]
    db.session.add_all(sample_patients)
    db.session.commit()

    # 3. Appointments
    today_str = date.today().strftime('%Y-%m-%d')
    sample_appointments = [
        Appointment(
            appointment_id="APT-1001",
            patient_id=sample_patients[0].id,
            doctor_id=sample_doctors[0].id,
            appointment_date=today_str,
            appointment_time="10:00 AM",
            reason="Routine ECG & Blood Pressure Checkup",
            status="Scheduled"
        ),
        Appointment(
            appointment_id="APT-1002",
            patient_id=sample_patients[1].id,
            doctor_id=sample_doctors[1].id,
            appointment_date=today_str,
            appointment_time="11:30 AM",
            reason="Allergy Consultation and Skin Patch Test",
            status="Completed"
        ),
        Appointment(
            appointment_id="APT-1003",
            patient_id=sample_patients[2].id,
            doctor_id=sample_doctors[2].id,
            appointment_date=today_str,
            appointment_time="02:00 PM",
            reason="Fever Evaluation & Blood Tests",
            status="Scheduled"
        ),
        Appointment(
            appointment_id="APT-1004",
            patient_id=sample_patients[3].id,
            doctor_id=sample_doctors[4].id,
            appointment_date=today_str,
            appointment_time="04:30 PM",
            reason="Knee X-Ray Review and Joint Mobility Consultation",
            status="Cancelled"
        )
    ]
    db.session.add_all(sample_appointments)
    db.session.commit()

    # 4. Bills
    sample_bills = [
        Bill(
            bill_id="BILL-1001",
            patient_id=sample_patients[0].id,
            doctor_id=sample_doctors[0].id,
            consultation_fee=800.0,
            medicine_charges=500.0,
            test_charges=650.0,
            other_charges=100.0,
            discount=150.0,
            total_amount=1900.0,
            payment_status="Paid",
            bill_date=datetime.now()
        ),
        Bill(
            bill_id="BILL-1002",
            patient_id=sample_patients[1].id,
            doctor_id=sample_doctors[1].id,
            consultation_fee=600.0,
            medicine_charges=350.0,
            test_charges=400.0,
            other_charges=50.0,
            discount=0.0,
            total_amount=1400.0,
            payment_status="Pending",
            bill_date=datetime.now()
        )
    ]
    db.session.add_all(sample_bills)
    db.session.commit()
    print("--- Sample data seeded successfully! ---")


# Automatically create tables and seed on application startup
with app.app_context():
    db.create_all()
    seed_initial_data()


if __name__ == '__main__':
    # Runs the local development server at port 5000
    app.run(debug=True, host='127.0.0.1', port=5000)
