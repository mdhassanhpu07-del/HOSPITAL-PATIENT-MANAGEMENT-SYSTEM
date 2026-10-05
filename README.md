# 🏥 Hospital Management System (HMS)

> A complete, beginner-friendly Hospital Management System developed using **Python**, **Flask**, **SQLite**, **HTML5**, **CSS3**, and **Bootstrap 5**. Designed specifically as a **BTech CSE Academic Project**.

---

## 📌 Project Overview

The **Hospital Management System (HMS)** is a web-based portal developed to streamline core hospital day-to-day operations. It allows hospital administrators to manage patient records, register doctors and their specialities, schedule patient appointments (with intelligent double-booking prevention), generate itemized hospital bills, and view real-time operational metrics on a dashboard.

---

## 🔑 Login Credentials

The application includes a single administrator authentication system using Flask sessions:

| Role | Username | Password |
| :--- | :--- | :--- |
| **Hospital Administrator** | `admin` | `admin123` |

---

## ✨ Key Features & Modules

### 1. 📊 Interactive Dashboard
- Summary stat cards displaying **Total Patients**, **Total Doctors**, **Today's Appointments**, and **Total Bills**.
- Quick action buttons to directly access Add Patient, Book Appointment, Add Doctor, and Generate Bill forms.
- Recent appointments and recently registered patients quick-look tables.

### 2. 🧑‍🤝‍🧑 Patient Management
- **Automatic ID generation**: `PAT-1001`, `PAT-1002`, etc.
- Stores Patient Name, Age, Gender, Phone, Address, Blood Group, Health Problem / Disease, and Registration Date.
- **Search Functionality**: Instant search by Patient Name, Phone Number, or Patient ID.
- **Patient Details Page**: Displays complete patient demographic info, medical problem, appointment history, and billing history.
- Full CRUD: Add, View, Edit, and Delete patient records.

### 3. 👨‍⚕️ Doctor Directory & Specialities
- **Doctor Attributes**: Doctor ID (`DOC-101`), Name, Speciality, Phone, Email, Consultation Fee, and Available Days.
- Pre-configured specialities:
  - *General Physician*
  - *Cardiologist*
  - *Dermatologist*
  - *Orthopedic*
  - *Pediatrician*
  - *Neurologist*
  - *ENT Specialist*
  - *Gynecologist*
- Doctor search by Name or Speciality.
- Full CRUD operations with fee validation.

### 4. 📅 Appointment Booking System
- Select patient and doctor from easy dropdowns.
- Pick appointment date and available time slot (`09:00 AM`, `10:00 AM`, etc.).
- **Duplicate Booking Prevention**: The system checks if the doctor already has an active appointment for the chosen date and time slot. If occupied, booking is rejected with a clear warning.
- Status management: `Scheduled`, `Completed`, or `Cancelled`.
- Search appointments by Patient Name, Doctor Name, Date, or Reason.

### 5. 🧾 Hospital Bill Generator & Printable Invoices
- Itemized billing breakdown:
  - Doctor Consultation Fee (auto-populated when doctor is selected)
  - Medicine Charges
  - Diagnostic / Lab Test Charges
  - Other Hospital Charges
  - Discount Amount
- **Live Automatic Calculation**: Total Amount = Consultation Fee + Medicine + Tests + Other - Discount.
- Prevents negative total amounts or negative charge entries.
- **Printable Bill**: A clean, professional invoice with hospital header, itemized receipt, totals, and signature stamp.
- Built-in **"Print Bill"** button using `window.print()` with print-friendly CSS.

---

## 📁 Project Structure

```text
hospital_management/
│
├── app.py                  # Main Flask application, routes, controllers & startup logic
├── models.py               # SQLAlchemy database models (Patient, Doctor, Appointment, Bill)
├── requirements.txt        # Python library dependencies
├── database.db             # SQLite database file (automatically created on first launch)
├── test_app.py             # Automated unit test suite (isolated in-memory tests)
├── test_all_features.py    # Complete 19-step verification script
│
├── templates/              # HTML Templates (Jinja2)
│   ├── base.html           # Base layout with navbar, notifications & footer
│   ├── login.html          # Admin login screen
│   ├── dashboard.html      # Overview metrics & quick action buttons
│   ├── patients.html       # Patient directory with search
│   ├── add_patient.html    # Patient registration form
│   ├── edit_patient.html   # Patient update form
│   ├── patient_details.html# Comprehensive patient profile & history
│   ├── doctors.html        # Doctors directory table
│   ├── add_doctor.html     # Doctor onboarding form
│   ├── edit_doctor.html    # Doctor update form
│   ├── appointments.html   # Appointments list & filters
│   ├── book_appointment.html# Appointment booking form with duplicate prevention
│   ├── edit_appointment.html# Appointment status/slot reschedule form
│   ├── bills.html          # Billing history list
│   ├── generate_bill.html  # Bill creation form with live calculation
│   └── bill_details.html   # Printable hospital invoice layout
│
└── static/                 # Static assets
    ├── css/
    │   └── style.css       # Custom styling, responsive rules & @media print styles
    └── js/
        └── script.js       # Dynamic bill calculation, fee auto-fill & print trigger
```

---

## 🗄️ Database Architecture (SQLite + SQLAlchemy)

The database schema uses simple, relational tables created automatically when the application starts:

1. **`patients`**
   - `id`: Primary key (Integer)
   - `patient_id`: Unique code (`PAT-1001`)
   - `name`, `age`, `gender`, `phone`, `address`, `blood_group`, `disease`, `registration_date`

2. **`doctors`**
   - `id`: Primary key (Integer)
   - `doctor_id`: Unique code (`DOC-101`)
   - `name`, `speciality`, `phone`, `email`, `consultation_fee`, `available_days`

3. **`appointments`**
   - `id`: Primary key (Integer)
   - `appointment_id`: Unique code (`APT-1001`)
   - `patient_id`: Foreign key -> `patients.id`
   - `doctor_id`: Foreign key -> `doctors.id`
   - `appointment_date`, `appointment_time`, `reason`, `status`, `created_at`

4. **`bills`**
   - `id`: Primary key (Integer)
   - `bill_id`: Unique code (`BILL-1001`)
   - `patient_id`: Foreign key -> `patients.id`
   - `doctor_id`: Foreign key -> `doctors.id`
   - `consultation_fee`, `medicine_charges`, `test_charges`, `other_charges`, `discount`, `total_amount`, `payment_status`, `bill_date`

---

## 🚀 How to Run the Project Locally

### Step 1: Clone or Navigate to the Project Folder
```bash
cd "d:\hospital management system"
```

### Step 2: (Optional but Recommended) Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate on Windows:
venv\Scripts\activate

# Or on macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the Application
```bash
python app.py
```

### Step 5: Open in Your Browser
Open your web browser and navigate to:
```text
http://127.0.0.1:5000
```
Log in using:
- **Username:** `admin`
- **Password:** `admin123`

---

## 🧪 Testing the Application

The project includes two automated test suites:

### 1. Isolated Unit Tests
```bash
python -m unittest -v test_app.py
```
*Runs all 8 unit tests in memory with 100% pass rate.*

### 2. Complete End-to-End Feature Verification
```bash
python test_all_features.py
```
*Tests and logs all 19 functional requirements: Login, Dashboard, Patient CRUD, Doctor CRUD, Duplicate Slot Blocking, Auto Calculation, and Bill Printing.*

---

## 💡 Viva Q&A / Explanation Guide

- **Q: Which framework and database are used?**  
  **A:** Python with Flask web framework and SQLite database via Flask-SQLAlchemy ORM.
- **Q: How does duplicate appointment prevention work?**  
  **A:** Before saving an appointment, the system executes a query filtering by `doctor_id`, `appointment_date`, and `appointment_time` where status is not `Cancelled`. If a matching record exists, an error message is returned.
- **Q: How is the bill calculated?**  
  **A:** On the client-side, JavaScript dynamically calculates `Total = Consultation + Medicine + Test + Other - Discount`. On form submission, Flask validates non-negative values and recomputes the final total on the server before committing to SQLite.
- **Q: How does bill printing work?**  
  **A:** The "Print Bill" button calls JavaScript's `window.print()`. CSS `@media print` rules automatically hide the navbar, action buttons, and footer, leaving a clean, hospital invoice page ready for PDF export or paper printing.
