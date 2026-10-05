"""
Comprehensive Test Suite for Hospital Management System.
Tests all requirements: Auth, Dashboard, Patients, Doctors, Appointments, Duplicate Prevention, Bills, and Calculations.
"""

import unittest
from datetime import date
from app import app, db
from models import Patient, Doctor, Appointment, Bill


class HospitalManagementSystemTestCase(unittest.TestCase):

    def setUp(self):
        # Configure app for isolated testing in memory
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()

        with app.app_context():
            db.create_all()
            from app import seed_initial_data
            seed_initial_data()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def login_admin(self):
        """Helper to log in as admin."""
        return self.client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)

    # ------------------------------------------------------
    # 1. AUTHENTICATION & ACCESS CONTROL TESTS
    # ------------------------------------------------------
    def test_01_access_protection_without_login(self):
        """Protected pages should redirect to login when unauthenticated."""
        response = self.client.get('/dashboard', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Please log in to access this page", response.data)
        self.assertIn(b"Admin Login", response.data)

    def test_02_invalid_login(self):
        """Invalid credentials should show error and reject login."""
        response = self.client.post('/login', data={
            'username': 'admin',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Invalid username or password", response.data)

    def test_03_valid_login_and_logout(self):
        """Admin should log in and log out cleanly."""
        # Login
        response = self.login_admin()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Login successful", response.data)
        self.assertIn(b"Hospital Dashboard", response.data)

        # Logout
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"You have been logged out successfully", response.data)

    # ------------------------------------------------------
    # 2. DASHBOARD & SEEDED SAMPLE DATA TESTS
    # ------------------------------------------------------
    def test_04_dashboard_metrics_and_sample_data(self):
        """Dashboard displays correct statistics and seeded sample records."""
        self.login_admin()
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)

        # Check metrics labels on dashboard
        self.assertIn(b"Total Patients", response.data)
        self.assertIn(b"Total Doctors", response.data)
        self.assertIn(b"Today's Appointments", response.data)
        self.assertIn(b"Total Bills", response.data)

        # Verify sample data exists in DB
        with app.app_context():
            self.assertGreaterEqual(Doctor.query.count(), 4)
            self.assertGreaterEqual(Patient.query.count(), 4)
            self.assertGreaterEqual(Appointment.query.count(), 2)
            self.assertGreaterEqual(Bill.query.count(), 2)

    # ------------------------------------------------------
    # 3. PATIENT RECORDS MANAGEMENT & SEARCH
    # ------------------------------------------------------
    def test_05_patient_crud_and_search(self):
        """Test adding, viewing, searching, editing, and deleting a patient."""
        self.login_admin()

        # Add Patient
        add_response = self.client.post('/patients/add', data={
            'name': 'Aarav Malhotra',
            'age': '29',
            'gender': 'Male',
            'phone': '9876549999',
            'address': 'Plot 44, Cyber City, Gurugram',
            'blood_group': 'B+',
            'disease': 'Sinusitis and severe migraine'
        }, follow_redirects=True)
        self.assertEqual(add_response.status_code, 200)
        self.assertIn(b"Aarav Malhotra", add_response.data)

        # Retrieve created patient
        with app.app_context():
            patient = Patient.query.filter_by(name='Aarav Malhotra').first()
            self.assertIsNotNone(patient)
            patient_id_num = patient.id
            patient_code = patient.patient_id

        # Search by name
        search_res = self.client.get(f'/patients?q=Aarav')
        self.assertIn(b"Aarav Malhotra", search_res.data)

        # Search by phone
        search_phone_res = self.client.get(f'/patients?q=9876549999')
        self.assertIn(b"Aarav Malhotra", search_phone_res.data)

        # Search by patient ID
        search_id_res = self.client.get(f'/patients?q={patient_code}')
        self.assertIn(b"Aarav Malhotra", search_id_res.data)

        # View Patient Details
        detail_res = self.client.get(f'/patients/{patient_id_num}')
        self.assertEqual(detail_res.status_code, 200)
        self.assertIn(b"Sinusitis and severe migraine", detail_res.data)

        # Edit Patient
        edit_res = self.client.post(f'/patients/edit/{patient_id_num}', data={
            'name': 'Aarav Malhotra',
            'age': '30',
            'gender': 'Male',
            'phone': '9876549999',
            'address': 'Plot 44, Cyber City, Gurugram',
            'blood_group': 'B+',
            'disease': 'Chronic Sinusitis (Updated)'
        }, follow_redirects=True)
        self.assertEqual(edit_res.status_code, 200)
        self.assertIn(b"Chronic Sinusitis (Updated)", edit_res.data)

        # Delete Patient
        del_res = self.client.post(f'/patients/delete/{patient_id_num}', follow_redirects=True)
        self.assertEqual(del_res.status_code, 200)
        with app.app_context():
            deleted = db.session.get(Patient, patient_id_num)
            self.assertIsNone(deleted)

    # ------------------------------------------------------
    # 4. DOCTORS MANAGEMENT & SEARCH
    # ------------------------------------------------------
    def test_06_doctor_crud_and_search(self):
        """Test adding, searching, editing, and removing a doctor."""
        self.login_admin()

        # Add Doctor
        add_doc = self.client.post('/doctors/add', data={
            'name': 'Kavita Iyer',
            'speciality': 'Neurologist',
            'phone': '9876512345',
            'email': 'kavita.iyer@hospital.com',
            'consultation_fee': '900.00',
            'available_days': 'Mon, Wed, Fri'
        }, follow_redirects=True)
        self.assertEqual(add_doc.status_code, 200)
        self.assertIn(b"Dr. Kavita Iyer", add_doc.data)

        with app.app_context():
            doc = Doctor.query.filter_by(phone='9876512345').first()
            self.assertIsNotNone(doc)
            doc_id = doc.id

        # Search Doctor by Name
        search_res = self.client.get('/doctors?q=Kavita')
        self.assertIn(b"Dr. Kavita Iyer", search_res.data)

        # Search Doctor by Speciality
        search_spec = self.client.get('/doctors?q=Neurologist')
        self.assertIn(b"Dr. Kavita Iyer", search_spec.data)

        # Edit Doctor
        edit_doc = self.client.post(f'/doctors/edit/{doc_id}', data={
            'name': 'Dr. Kavita Iyer',
            'speciality': 'Neurologist',
            'phone': '9876512345',
            'email': 'kavita.iyer@hospital.com',
            'consultation_fee': '950.00',
            'available_days': 'Mon to Saturday'
        }, follow_redirects=True)
        self.assertEqual(edit_doc.status_code, 200)
        self.assertIn(b"950.00", edit_doc.data)

        # Delete Doctor
        del_doc = self.client.post(f'/doctors/delete/{doc_id}', follow_redirects=True)
        self.assertEqual(del_doc.status_code, 200)
        with app.app_context():
            self.assertIsNone(db.session.get(Doctor, doc_id))

    # ------------------------------------------------------
    # 5. APPOINTMENT BOOKING & DUPLICATE PREVENTIONS
    # ------------------------------------------------------
    def test_07_appointment_booking_and_duplicate_prevention(self):
        """Test booking appointments and preventing duplicate bookings for the same doctor at the same slot."""
        self.login_admin()

        with app.app_context():
            patient = Patient.query.first()
            doctor = Doctor.query.first()
            patient2 = Patient.query.offset(1).first()
            pid = patient.id
            p2id = patient2.id
            did = doctor.id

        test_date = '2026-11-20'
        test_time = '10:00 AM'

        # Book first appointment
        book_res1 = self.client.post('/appointments/book', data={
            'patient_id': pid,
            'doctor_id': did,
            'appointment_date': test_date,
            'appointment_time': test_time,
            'reason': 'Follow-up cardiology consultation'
        }, follow_redirects=True)
        self.assertEqual(book_res1.status_code, 200)
        self.assertIn(b"Appointment booked successfully", book_res1.data)

        # Attempt DUPLICATE booking for same doctor on same date and same time!
        book_res_dup = self.client.post('/appointments/book', data={
            'patient_id': p2id,
            'doctor_id': did,
            'appointment_date': test_date,
            'appointment_time': test_time,
            'reason': 'Another appointment for same slot'
        }, follow_redirects=True)
        self.assertEqual(book_res_dup.status_code, 200)
        # Duplicate must be blocked with an informative flash message!
        self.assertIn(b"Slot conflict", book_res_dup.data)

        # Check Appointment Status Changes
        with app.app_context():
            apt = Appointment.query.filter_by(
                doctor_id=did,
                appointment_date=test_date,
                appointment_time=test_time
            ).first()
            self.assertIsNotNone(apt)
            apt_id = apt.id

        # Mark as Completed
        status_res = self.client.post(f'/appointments/status/{apt_id}/Completed', follow_redirects=True)
        self.assertEqual(status_res.status_code, 200)
        self.assertIn(b"Appointment status updated to Completed", status_res.data)

        # Cancel appointment
        cancel_res = self.client.post(f'/appointments/status/{apt_id}/Cancelled', follow_redirects=True)
        self.assertEqual(cancel_res.status_code, 200)
        self.assertIn(b"Appointment status updated to Cancelled", cancel_res.data)

    # ------------------------------------------------------
    # 6. BILL GENERATOR & AUTOMATIC CALCULATION
    # ------------------------------------------------------
    def test_08_bill_generator_and_calculation(self):
        """Test bill generation, server-side auto-calculation, and printable bill view."""
        self.login_admin()

        with app.app_context():
            patient = Patient.query.first()
            doctor = Doctor.query.first()
            pid = patient.id
            did = doctor.id

        # Total formula: Consultation (800) + Medicine (300) + Test (400) + Other (100) - Discount (100) = 1500.00
        bill_res = self.client.post('/bills/generate', data={
            'patient_id': pid,
            'doctor_id': did,
            'consultation_fee': '800.00',
            'medicine_charges': '300.00',
            'test_charges': '400.00',
            'other_charges': '100.00',
            'discount': '100.00',
            'payment_status': 'Paid'
        }, follow_redirects=True)
        self.assertEqual(bill_res.status_code, 200)
        self.assertIn(b"generated successfully", bill_res.data)
        self.assertIn(b"1500.00", bill_res.data)
        self.assertIn(b"Print Bill", bill_res.data)

        # Check DB values
        with app.app_context():
            bill = Bill.query.order_by(Bill.id.desc()).first()
            self.assertEqual(bill.total_amount, 1500.0)
            self.assertEqual(bill.payment_status, 'Paid')
            bill_id_num = bill.id

        # Toggle payment status to Pending
        stat_res = self.client.post(f'/bills/status/{bill_id_num}/Pending', follow_redirects=True)
        self.assertEqual(stat_res.status_code, 200)
        self.assertIn(b"PAYMENT PENDING", stat_res.data)

    # ------------------------------------------------------
    # 7. PATIENT LOGIN & PATIENT PORTAL
    # ------------------------------------------------------
    def test_09_patient_login_and_portal(self):
        """Test patient login using Patient ID and phone number, viewing their portal, and booking an appointment."""
        # 1. Invalid Patient Login
        res_invalid = self.client.post('/login', data={
            'login_type': 'patient',
            'patient_id': 'PAT-9999',
            'phone': '1234567890'
        }, follow_redirects=True)
        self.assertEqual(res_invalid.status_code, 200)
        self.assertIn(b"Invalid Patient ID or Phone Number", res_invalid.data)

        # 2. Valid Patient Login with Rajesh Kumar (PAT-1001 / 9811223344)
        res_valid = self.client.post('/login', data={
            'login_type': 'patient',
            'patient_id': 'PAT-1001',
            'phone': '9811223344'
        }, follow_redirects=True)
        self.assertEqual(res_valid.status_code, 200)
        self.assertIn(b"Welcome back, Rajesh Kumar", res_valid.data)
        self.assertIn(b"My Booked Appointments", res_valid.data)
        self.assertIn(b"My Hospital Invoices", res_valid.data)

        # 3. Patient views their own bill
        with app.app_context():
            bill = Bill.query.filter_by(patient_id=1).first()
            b_id = bill.id
        bill_res = self.client.get(f'/bills/{b_id}')
        self.assertEqual(bill_res.status_code, 200)
        self.assertIn(b"MEDITRACK", bill_res.data)

        # 4. Patient self-booking appointment
        apt_res = self.client.post('/patient/book-appointment', data={
            'doctor_id': 2,
            'appointment_date': '2026-12-01',
            'appointment_time': '03:00 PM',
            'reason': 'Skin checkup consultation'
        }, follow_redirects=True)
        self.assertEqual(apt_res.status_code, 200)
        self.assertIn(b"Appointment booked successfully", apt_res.data)
        self.assertIn(b"Skin checkup consultation", apt_res.data)


if __name__ == '__main__':
    unittest.main()
