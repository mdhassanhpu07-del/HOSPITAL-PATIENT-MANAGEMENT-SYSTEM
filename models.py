from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

# ==========================================================
# 1. PATIENT MODEL
# ==========================================================
class Patient(db.Model):
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    blood_group = db.Column(db.String(10), nullable=False)
    disease = db.Column(db.Text, nullable=False)  # Disease / Problem
    registration_date = db.Column(db.DateTime, default=datetime.now)

    # Relationships: If a patient is deleted, their appointments and bills are also deleted
    appointments = db.relationship('Appointment', backref='patient', lazy=True, cascade='all, delete-orphan')
    bills = db.relationship('Bill', backref='patient', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Patient {self.patient_id} - {self.name}>"


# ==========================================================
# 2. DOCTOR MODEL
# ==========================================================
class Doctor(db.Model):
    __tablename__ = 'doctors'

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    speciality = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    consultation_fee = db.Column(db.Float, nullable=False, default=500.0)
    available_days = db.Column(db.String(100), nullable=False)

    # Relationships
    appointments = db.relationship('Appointment', backref='doctor', lazy=True, cascade='all, delete-orphan')
    bills = db.relationship('Bill', backref='doctor', lazy=True)

    def __repr__(self):
        return f"<Doctor {self.doctor_id} - {self.name}>"


# ==========================================================
# 3. APPOINTMENT MODEL
# ==========================================================
class Appointment(db.Model):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.String(20), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False)
    appointment_date = db.Column(db.String(20), nullable=False)  # Format: YYYY-MM-DD
    appointment_time = db.Column(db.String(20), nullable=False)  # Format: HH:MM or slot
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Scheduled')  # Scheduled, Completed, Cancelled
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f"<Appointment {self.appointment_id} - {self.status}>"


# ==========================================================
# 4. BILL MODEL
# ==========================================================
class Bill(db.Model):
    __tablename__ = 'bills'

    id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.String(20), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id', ondelete='SET NULL'), nullable=True)
    consultation_fee = db.Column(db.Float, default=0.0)
    medicine_charges = db.Column(db.Float, default=0.0)
    test_charges = db.Column(db.Float, default=0.0)
    other_charges = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(20), nullable=False, default='Paid')  # Paid, Pending
    bill_date = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f"<Bill {self.bill_id} - {self.total_amount}>"


# ==========================================================
# HELPER FUNCTIONS TO GENERATE CLEAN UNIQUE IDS
# ==========================================================
def generate_patient_id():
    last = Patient.query.order_by(Patient.id.desc()).first()
    next_num = (last.id + 1) if last else 1
    return f"PAT-{1000 + next_num}"

def generate_doctor_id():
    last = Doctor.query.order_by(Doctor.id.desc()).first()
    next_num = (last.id + 1) if last else 1
    return f"DOC-{100 + next_num}"

def generate_appointment_id():
    last = Appointment.query.order_by(Appointment.id.desc()).first()
    next_num = (last.id + 1) if last else 1
    return f"APT-{1000 + next_num}"

def generate_bill_id():
    last = Bill.query.order_by(Bill.id.desc()).first()
    next_num = (last.id + 1) if last else 1
    return f"BILL-{1000 + next_num}"
