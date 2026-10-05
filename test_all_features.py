"""
Verification Script to test and log every single requirement from the user prompt.
"""

from app import app, db
from models import Patient, Doctor, Appointment, Bill
from datetime import date

def test_checklist():
    client = app.test_client()

    print("\n=======================================================")
    print("      RUNNING HOSPITAL MANAGEMENT SYSTEM VERIFICATION   ")
    print("=======================================================\n")

    # 1. Login
    res = client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    assert res.status_code == 200 and b"Hospital Dashboard" in res.data
    print("[PASS] 1. Login (admin/admin123)")

    # 2. Dashboard
    res = client.get('/dashboard')
    assert res.status_code == 200 and b"Total Patients" in res.data and b"Total Doctors" in res.data
    print("[PASS] 2. Dashboard metrics and quick action buttons")

    # 3. Add patient
    res = client.post('/patients/add', data={
        'name': 'Sanjay Verma',
        'age': '48',
        'gender': 'Male',
        'phone': '9876543200',
        'address': '22 Gandhi Road, Pune',
        'blood_group': 'O+',
        'disease': 'Type 2 Diabetes & Fatigue'
    }, follow_redirects=True)
    assert res.status_code == 200 and b"Sanjay Verma" in res.data
    with app.app_context():
        p = Patient.query.filter_by(name='Sanjay Verma').first()
        p_id = p.id
        p_code = p.patient_id
    print(f"[PASS] 3. Add Patient ({p_code}: Sanjay Verma)")

    # 4. View patient details
    res = client.get(f'/patients/{p_id}')
    assert res.status_code == 200 and b"Type 2 Diabetes" in res.data
    print("[PASS] 4. View Patient Details")

    # 5. Search patient (by ID, Name, Phone)
    res_name = client.get('/patients?q=Sanjay')
    assert b"Sanjay Verma" in res_name.data
    res_phone = client.get('/patients?q=9876543200')
    assert b"Sanjay Verma" in res_phone.data
    res_id = client.get(f'/patients?q={p_code}')
    assert b"Sanjay Verma" in res_id.data
    print("[PASS] 5. Search Patient (by Name, Phone, and Patient ID)")

    # 6. Edit patient
    res = client.post(f'/patients/edit/{p_id}', data={
        'name': 'Sanjay Verma',
        'age': '49',
        'gender': 'Male',
        'phone': '9876543200',
        'address': '22 Gandhi Road, Pune (Updated)',
        'blood_group': 'O+',
        'disease': 'Type 2 Diabetes Controlled'
    }, follow_redirects=True)
    assert res.status_code == 200 and b"Type 2 Diabetes Controlled" in res.data
    print("[PASS] 6. Edit Patient")

    # 7. Add doctor
    res = client.post('/doctors/add', data={
        'name': 'Rohan Deshmukh',
        'speciality': 'ENT Specialist',
        'phone': '9876549999',
        'email': 'rohan.deshmukh@hospital.com',
        'consultation_fee': '650.00',
        'available_days': 'Mon - Sat'
    }, follow_redirects=True)
    assert res.status_code == 200 and b"Dr. Rohan Deshmukh" in res.data
    with app.app_context():
        d = Doctor.query.filter_by(phone='9876549999').first()
        d_id = d.id
    print(f"[PASS] 7. Add Doctor (Dr. Rohan Deshmukh, ENT Specialist)")

    # 8. Search doctor (by Name and Speciality)
    res_doc_name = client.get('/doctors?q=Deshmukh')
    assert b"Dr. Rohan Deshmukh" in res_doc_name.data
    res_doc_spec = client.get('/doctors?q=ENT')
    assert b"Dr. Rohan Deshmukh" in res_doc_spec.data
    print("[PASS] 8. Search Doctor (by Name and Speciality)")

    # 9. Edit doctor
    res = client.post(f'/doctors/edit/{d_id}', data={
        'name': 'Dr. Rohan Deshmukh',
        'speciality': 'ENT Specialist',
        'phone': '9876549999',
        'email': 'rohan.deshmukh@hospital.com',
        'consultation_fee': '700.00',
        'available_days': 'Mon, Wed, Fri'
    }, follow_redirects=True)
    assert res.status_code == 200 and b"700.00" in res.data
    print("[PASS] 9. Edit Doctor")

    # 10. Book appointment
    apt_date = '2026-11-25'
    apt_time = '11:00 AM'
    with app.app_context():
        # Ensure slot is clear from previous test run
        Appointment.query.filter_by(doctor_id=d_id, appointment_date=apt_date, appointment_time=apt_time).delete()
        db.session.commit()

    res = client.post('/appointments/book', data={
        'patient_id': p_id,
        'doctor_id': d_id,
        'appointment_date': apt_date,
        'appointment_time': apt_time,
        'reason': 'Throat infection consultation'
    }, follow_redirects=True)
    assert res.status_code == 200 and b"Appointment booked successfully" in res.data
    with app.app_context():
        apt = Appointment.query.filter_by(doctor_id=d_id, appointment_date=apt_date, appointment_time=apt_time).first()
        apt_id = apt.id
    print(f"[PASS] 10. Book Appointment ({apt.appointment_id})")

    # 11. Prevent duplicate doctor appointment
    res_dup = client.post('/appointments/book', data={
        'patient_id': 1,
        'doctor_id': d_id,
        'appointment_date': apt_date,
        'appointment_time': apt_time,
        'reason': 'Attempting double booking'
    }, follow_redirects=True)
    assert res_dup.status_code == 200 and b"Slot conflict" in res_dup.data
    print("[PASS] 11. Prevent Duplicate Doctor Appointment (Blocked slot conflict)")

    # 12. Search/filter appointments
    res_apt_search = client.get('/appointments?q=Throat')
    assert b"Throat infection" in res_apt_search.data
    res_apt_filter = client.get('/appointments?status=Scheduled')
    assert b"Scheduled" in res_apt_filter.data
    print("[PASS] 12. Search & Filter Appointments")

    # 13. Edit appointment
    res = client.post(f'/appointments/edit/{apt_id}', data={
        'patient_id': p_id,
        'doctor_id': d_id,
        'appointment_date': apt_date,
        'appointment_time': '11:30 AM',
        'status': 'Scheduled',
        'reason': 'Throat and ear infection checkup'
    }, follow_redirects=True)
    assert res.status_code == 200 and b"Appointment updated successfully" in res.data
    print("[PASS] 13. Edit Appointment")

    # 14. Mark appointment completed
    res = client.post(f'/appointments/status/{apt_id}/Completed', follow_redirects=True)
    assert res.status_code == 200 and b"status updated to Completed" in res.data
    print("[PASS] 14. Mark Appointment as Completed")

    # 15. Cancel appointment
    res = client.post(f'/appointments/status/{apt_id}/Cancelled', follow_redirects=True)
    assert res.status_code == 200 and b"status updated to Cancelled" in res.data
    print("[PASS] 15. Cancel Appointment")

    # 16. Generate bill with automatic calculation
    # Consultation: 700, Medicine: 250, Test: 300, Other: 50, Discount: 100 => Total = 1200.00
    res = client.post('/bills/generate', data={
        'patient_id': p_id,
        'doctor_id': d_id,
        'consultation_fee': '700.00',
        'medicine_charges': '250.00',
        'test_charges': '300.00',
        'other_charges': '50.00',
        'discount': '100.00',
        'payment_status': 'Paid'
    }, follow_redirects=True)
    assert res.status_code == 200 and b"1200.00" in res.data
    with app.app_context():
        bill = Bill.query.filter_by(patient_id=p_id).order_by(Bill.id.desc()).first()
        b_id = bill.id
        assert bill.total_amount == 1200.0
    print(f"[PASS] 16. Generate Bill & Automatic Calculation (Total: Rs. 1200.00)")

    # 17. View & Print bill
    res = client.get(f'/bills/{b_id}')
    assert res.status_code == 200 and b"MEDITRACK" in res.data and b"window.print()" in res.data
    print("[PASS] 17. View Bill & Printable Invoice (with Print Bill button & MEDITRACK branding)")

    # 18. Delete records
    res_del_apt = client.post(f'/appointments/delete/{apt_id}', follow_redirects=True)
    assert res_del_apt.status_code == 200
    res_del_doc = client.post(f'/doctors/delete/{d_id}', follow_redirects=True)
    assert res_del_doc.status_code == 200
    res_del_pat = client.post(f'/patients/delete/{p_id}', follow_redirects=True)
    assert res_del_pat.status_code == 200
    print("[PASS] 18. Delete Appointment, Doctor, and Patient")

    # 19. Admin Logout
    res_logout = client.get('/logout', follow_redirects=True)
    assert res_logout.status_code == 200 and b"logged out successfully" in res_logout.data
    print("[PASS] 19. Admin Logout")

    # 20. Patient Login & Patient Portal Verification
    res_pat_login = client.post('/login', data={
        'login_type': 'patient',
        'patient_id': 'PAT-1001',
        'phone': '9811223344'
    }, follow_redirects=True)
    assert res_pat_login.status_code == 200 and b"Welcome, Rajesh Kumar" in res_pat_login.data
    assert b"My Booked Appointments" in res_pat_login.data
    print("[PASS] 20. Patient Login & Patient Portal (PAT-1001 / 9811223344)")

    # Patient Logout
    res_pat_logout = client.get('/logout', follow_redirects=True)
    assert res_pat_logout.status_code == 200
    print("[PASS] 21. Patient Logout")

    print("\n=======================================================")
    print("  ALL 21 VERIFICATION STEPS PASSED SUCCESSFULLY! (100%) ")
    print("=======================================================\n")

if __name__ == '__main__':
    test_checklist()
