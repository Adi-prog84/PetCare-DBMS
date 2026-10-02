"""
PetCare+ — Smart Pet Clinic Management System
Main Flask Application
College DBMS Project
"""

from functools import wraps
from datetime import date, datetime
from flask import (
    Flask, render_template, request, redirect, 
    url_for, session, flash, jsonify
)
from werkzeug.security import check_password_hash, generate_password_hash
import mysql.connector

from config import Config
from db import query_db, get_db_connection

app = Flask(__name__)
app.config.from_object(Config)

# --------------------------------------------------------------------
# Authentication and Role-based Access Control Helpers
# --------------------------------------------------------------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def roles_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('login'))
            if session.get('role') not in allowed_roles:
                flash('Access Denied: You do not have permission to view that resource.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.context_processor
def inject_user():
    """Make current user and today's date available across all templates."""
    return {
        'current_user': {
            'id': session.get('user_id'),
            'username': session.get('username'),
            'full_name': session.get('full_name'),
            'role': session.get('role')
        },
        'today_date': date.today().strftime('%Y-%m-%d')
    }

# --------------------------------------------------------------------
# 1. Authentication Routes
# --------------------------------------------------------------------

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Please provide both username and password.', 'warning')
            return render_template('login.html')

        try:
            user = query_db(
                "SELECT user_id, username, password, role, full_name FROM users WHERE username = %s",
                (username,),
                one=True
            )

            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['user_id']
                session['username'] = user['username']
                session['role'] = user['role']
                session['full_name'] = user['full_name']
                flash(f"Welcome back, {user['full_name']} ({user['role']})!", 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password.', 'danger')
        except Exception as e:
            flash(f'Database connection error: {str(e)}', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

# --------------------------------------------------------------------
# 2. Dashboard
# --------------------------------------------------------------------

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # Aggregations for cards
        counts = {
            'pets': query_db("SELECT COUNT(*) AS total FROM pets", one=True)['total'],
            'owners': query_db("SELECT COUNT(*) AS total FROM pet_owners", one=True)['total'],
            'vets': query_db("SELECT COUNT(*) AS total FROM veterinarians", one=True)['total'],
            'today_appts': query_db(
                "SELECT COUNT(*) AS total FROM appointments WHERE appointment_date = CURDATE()", 
                one=True
            )['total'],
            'pending_appts': query_db(
                "SELECT COUNT(*) AS total FROM appointments WHERE status = 'Scheduled'", 
                one=True
            )['total'],
            'unpaid_bills': query_db(
                "SELECT COUNT(*) AS total, COALESCE(SUM(total_amount), 0) AS amount FROM bills WHERE payment_status = 'Unpaid'", 
                one=True
            ),
            'upcoming_vax': query_db(
                """SELECT COUNT(*) AS total FROM vaccinations 
                   WHERE next_due_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)""", 
                one=True
            )['total']
        }

        # Today's appointments schedule
        today_appointments = query_db(
            """SELECT a.appointment_id, a.appointment_time, a.reason, a.status,
                      p.pet_name, p.species, o.name AS owner_name, v.name AS vet_name
               FROM appointments a
               JOIN pets p ON a.pet_id = p.pet_id
               JOIN pet_owners o ON p.owner_id = o.owner_id
               JOIN veterinarians v ON a.vet_id = v.vet_id
               WHERE a.appointment_date = CURDATE()
               ORDER BY a.appointment_time ASC"""
        )

        # Recent appointments
        recent_appointments = query_db(
            """SELECT a.appointment_id, a.appointment_date, a.appointment_time, a.reason, a.status,
                      p.pet_name, p.species, o.name AS owner_name, v.name AS vet_name
               FROM appointments a
               JOIN pets p ON a.pet_id = p.pet_id
               JOIN pet_owners o ON p.owner_id = o.owner_id
               JOIN veterinarians v ON a.vet_id = v.vet_id
               ORDER BY a.appointment_date DESC, a.appointment_time DESC
               LIMIT 5"""
        )

        # Urgent vaccinations (overdue or within 14 days)
        urgent_vaccinations = query_db(
            """SELECT v.vaccination_id, v.vaccine_name, v.next_due_date,
                      p.pet_name, p.species, o.name AS owner_name, o.phone AS owner_phone,
                      DATEDIFF(v.next_due_date, CURDATE()) AS days_left
               FROM vaccinations v
               JOIN pets p ON v.pet_id = p.pet_id
               JOIN pet_owners o ON p.owner_id = o.owner_id
               WHERE v.next_due_date <= DATE_ADD(CURDATE(), INTERVAL 14 DAY)
               ORDER BY v.next_due_date ASC
               LIMIT 5"""
        )

        return render_template(
            'dashboard.html',
            counts=counts,
            today_appointments=today_appointments,
            recent_appointments=recent_appointments,
            urgent_vaccinations=urgent_vaccinations
        )
    except Exception as e:
        flash(f"Error loading dashboard metrics: {e}", "danger")
        return render_template('dashboard.html', counts={}, today_appointments=[], recent_appointments=[], urgent_vaccinations=[])

# --------------------------------------------------------------------
# 3. Pet Owner Management
# --------------------------------------------------------------------

@app.route('/owners')
@login_required
@roles_required('Admin', 'Receptionist')
def owners():
    search = request.args.get('search', '').strip()
    if search:
        search_wildcard = f"%{search}%"
        owners_list = query_db(
            """SELECT o.*, COUNT(p.pet_id) AS pet_count 
               FROM pet_owners o 
               LEFT JOIN pets p ON o.owner_id = p.owner_id 
               WHERE o.name LIKE %s OR o.phone LIKE %s OR o.email LIKE %s OR o.address LIKE %s
               GROUP BY o.owner_id 
               ORDER BY o.name ASC""",
            (search_wildcard, search_wildcard, search_wildcard, search_wildcard)
        )
    else:
        owners_list = query_db(
            """SELECT o.*, COUNT(p.pet_id) AS pet_count 
               FROM pet_owners o 
               LEFT JOIN pets p ON o.owner_id = p.owner_id 
               GROUP BY o.owner_id 
               ORDER BY o.name ASC"""
        )
    return render_template('owners.html', owners=owners_list, search=search)

@app.route('/owners/add', methods=['POST'])
@login_required
@roles_required('Admin', 'Receptionist')
def add_owner():
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    address = request.form.get('address', '').strip()

    if not name or not phone or not email or not address:
        flash('All owner fields are required.', 'danger')
        return redirect(url_for('owners'))

    try:
        query_db(
            "INSERT INTO pet_owners (name, phone, email, address) VALUES (%s, %s, %s, %s)",
            (name, phone, email, address),
            commit=True
        )
        flash(f'Pet owner "{name}" added successfully.', 'success')
    except mysql.connector.Error as err:
        if err.errno == 1062:
            flash(f'Error: An owner with email "{email}" already exists.', 'danger')
        else:
            flash(f'Database error: {err}', 'danger')

    return redirect(url_for('owners'))

@app.route('/owners/edit/<int:owner_id>', methods=['POST'])
@login_required
@roles_required('Admin', 'Receptionist')
def edit_owner(owner_id):
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    address = request.form.get('address', '').strip()

    try:
        query_db(
            "UPDATE pet_owners SET name = %s, phone = %s, email = %s, address = %s WHERE owner_id = %s",
            (name, phone, email, address, owner_id),
            commit=True
        )
        flash('Owner details updated successfully.', 'success')
    except mysql.connector.Error as err:
        if err.errno == 1062:
            flash(f'Error: Email "{email}" is already used by another owner.', 'danger')
        else:
            flash(f'Database error: {err}', 'danger')

    return redirect(url_for('owners'))

@app.route('/owners/delete/<int:owner_id>', methods=['POST'])
@login_required
@roles_required('Admin')
def delete_owner(owner_id):
    try:
        query_db("DELETE FROM pet_owners WHERE owner_id = %s", (owner_id,), commit=True)
        flash('Owner and all associated pets deleted successfully.', 'success')
    except Exception as e:
        flash(f'Error deleting owner: {e}', 'danger')
    return redirect(url_for('owners'))

@app.route('/owners/<int:owner_id>/pets')
@login_required
def owner_pets(owner_id):
    """API endpoint to get pets for an owner (used dynamically in appointment booking)."""
    pets_list = query_db(
        "SELECT pet_id, pet_name, species, breed FROM pets WHERE owner_id = %s ORDER BY pet_name",
        (owner_id,)
    )
    return jsonify(pets_list)

# --------------------------------------------------------------------
# 4. Pet Management
# --------------------------------------------------------------------

@app.route('/pets')
@login_required
def pets():
    search = request.args.get('search', '').strip()
    species_filter = request.args.get('species', '').strip()

    sql = """SELECT p.*, o.name AS owner_name, o.phone AS owner_phone 
             FROM pets p 
             JOIN pet_owners o ON p.owner_id = o.owner_id 
             WHERE 1=1"""
    params = []

    if search:
        sql += " AND (p.pet_name LIKE %s OR p.breed LIKE %s OR o.name LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    
    if species_filter:
        sql += " AND p.species = %s"
        params.append(species_filter)

    sql += " ORDER BY p.pet_name ASC"
    pets_list = query_db(sql, tuple(params))

    # Get all owners for the Add Pet modal
    all_owners = query_db("SELECT owner_id, name, phone FROM pet_owners ORDER BY name ASC")
    
    # Get distinct species for the filter dropdown
    species_list = query_db("SELECT DISTINCT species FROM pets ORDER BY species ASC")

    return render_template(
        'pets.html', 
        pets=pets_list, 
        owners=all_owners, 
        species_list=species_list, 
        search=search, 
        species_filter=species_filter
    )

@app.route('/pets/add', methods=['POST'])
@login_required
@roles_required('Admin', 'Receptionist')
def add_pet():
    owner_id = request.form.get('owner_id')
    pet_name = request.form.get('pet_name', '').strip()
    species = request.form.get('species', '').strip()
    breed = request.form.get('breed', '').strip() or 'Unknown'
    gender = request.form.get('gender', 'Unknown')
    dob = request.form.get('date_of_birth') or None
    weight = request.form.get('weight') or None

    if not owner_id or not pet_name or not species:
        flash('Owner, Pet Name, and Species are required.', 'danger')
        return redirect(url_for('pets'))

    try:
        query_db(
            """INSERT INTO pets (owner_id, pet_name, species, breed, gender, date_of_birth, weight) 
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (owner_id, pet_name, species, breed, gender, dob, weight),
            commit=True
        )
        flash(f'Pet "{pet_name}" added successfully.', 'success')
    except Exception as e:
        flash(f'Error adding pet: {e}', 'danger')

    return redirect(url_for('pets'))

@app.route('/pets/edit/<int:pet_id>', methods=['POST'])
@login_required
@roles_required('Admin', 'Receptionist', 'Veterinarian')
def edit_pet(pet_id):
    owner_id = request.form.get('owner_id')
    pet_name = request.form.get('pet_name', '').strip()
    species = request.form.get('species', '').strip()
    breed = request.form.get('breed', '').strip() or 'Unknown'
    gender = request.form.get('gender', 'Unknown')
    dob = request.form.get('date_of_birth') or None
    weight = request.form.get('weight') or None

    try:
        query_db(
            """UPDATE pets 
               SET owner_id = %s, pet_name = %s, species = %s, breed = %s, 
                   gender = %s, date_of_birth = %s, weight = %s 
               WHERE pet_id = %s""",
            (owner_id, pet_name, species, breed, gender, dob, weight, pet_id),
            commit=True
        )
        flash(f'Pet "{pet_name}" updated successfully.', 'success')
    except Exception as e:
        flash(f'Error updating pet: {e}', 'danger')

    return redirect(url_for('pets'))

@app.route('/pets/delete/<int:pet_id>', methods=['POST'])
@login_required
@roles_required('Admin')
def delete_pet(pet_id):
    try:
        query_db("DELETE FROM pets WHERE pet_id = %s", (pet_id,), commit=True)
        flash('Pet and all medical records deleted successfully.', 'success')
    except Exception as e:
        flash(f'Error deleting pet: {e}', 'danger')
    return redirect(url_for('pets'))

@app.route('/pets/<int:pet_id>')
@login_required
def pet_detail(pet_id):
    """Comprehensive Medical Record Dossier for a specific pet."""
    pet = query_db(
        """SELECT p.*, o.name AS owner_name, o.phone AS owner_phone, o.email AS owner_email, o.address AS owner_address
           FROM pets p
           JOIN pet_owners o ON p.owner_id = o.owner_id
           WHERE p.pet_id = %s""",
        (pet_id,),
        one=True
    )
    if not pet:
        flash('Pet record not found.', 'danger')
        return redirect(url_for('pets'))

    appointments_history = query_db(
        """SELECT a.*, v.name AS vet_name, v.specialization, t.treatment_id, t.diagnosis, b.bill_id, b.total_amount, b.payment_status
           FROM appointments a
           JOIN veterinarians v ON a.vet_id = v.vet_id
           LEFT JOIN treatments t ON a.appointment_id = t.appointment_id
           LEFT JOIN bills b ON a.appointment_id = b.appointment_id
           WHERE a.pet_id = %s
           ORDER BY a.appointment_date DESC, a.appointment_time DESC""",
        (pet_id,)
    )

    vaccinations_history = query_db(
        """SELECT *, DATEDIFF(next_due_date, CURDATE()) AS days_until_due
           FROM vaccinations 
           WHERE pet_id = %s 
           ORDER BY vaccination_date DESC""",
        (pet_id,)
    )

    treatments_history = query_db(
        """SELECT t.*, a.appointment_date, v.name AS vet_name
           FROM treatments t
           JOIN appointments a ON t.appointment_id = a.appointment_id
           JOIN veterinarians v ON a.vet_id = v.vet_id
           WHERE a.pet_id = %s
           ORDER BY t.treatment_date DESC""",
        (pet_id,)
    )

    return render_template(
        'pet_detail.html',
        pet=pet,
        appointments=appointments_history,
        vaccinations=vaccinations_history,
        treatments=treatments_history
    )

# --------------------------------------------------------------------
# 5. Veterinarian Management
# --------------------------------------------------------------------

@app.route('/veterinarians')
@login_required
def veterinarians():
    search = request.args.get('search', '').strip()
    if search:
        search_wildcard = f"%{search}%"
        vets = query_db(
            """SELECT v.*, COUNT(a.appointment_id) AS total_appointments 
               FROM veterinarians v 
               LEFT JOIN appointments a ON v.vet_id = a.vet_id 
               WHERE v.name LIKE %s OR v.specialization LIKE %s OR v.email LIKE %s
               GROUP BY v.vet_id 
               ORDER BY v.name ASC""",
            (search_wildcard, search_wildcard, search_wildcard)
        )
    else:
        vets = query_db(
            """SELECT v.*, COUNT(a.appointment_id) AS total_appointments 
               FROM veterinarians v 
               LEFT JOIN appointments a ON v.vet_id = a.vet_id 
               GROUP BY v.vet_id 
               ORDER BY v.name ASC"""
        )
    return render_template('veterinarians.html', veterinarians=vets, search=search)

@app.route('/veterinarians/add', methods=['POST'])
@login_required
@roles_required('Admin')
def add_veterinarian():
    name = request.form.get('name', '').strip()
    specialization = request.form.get('specialization', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()

    if not name or not specialization or not phone or not email:
        flash('All veterinarian fields are required.', 'danger')
        return redirect(url_for('veterinarians'))

    try:
        query_db(
            "INSERT INTO veterinarians (name, specialization, phone, email) VALUES (%s, %s, %s, %s)",
            (name, specialization, phone, email),
            commit=True
        )
        flash(f'Dr. {name} added successfully.', 'success')
    except mysql.connector.Error as err:
        if err.errno == 1062:
            flash(f'A veterinarian with email "{email}" already exists.', 'danger')
        else:
            flash(f'Database error: {err}', 'danger')

    return redirect(url_for('veterinarians'))

@app.route('/veterinarians/edit/<int:vet_id>', methods=['POST'])
@login_required
@roles_required('Admin')
def edit_veterinarian(vet_id):
    name = request.form.get('name', '').strip()
    specialization = request.form.get('specialization', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()

    try:
        query_db(
            "UPDATE veterinarians SET name = %s, specialization = %s, phone = %s, email = %s WHERE vet_id = %s",
            (name, specialization, phone, email, vet_id),
            commit=True
        )
        flash(f'Veterinarian {name} updated successfully.', 'success')
    except mysql.connector.Error as err:
        if err.errno == 1062:
            flash(f'A veterinarian with email "{email}" already exists.', 'danger')
        else:
            flash(f'Database error: {err}', 'danger')

    return redirect(url_for('veterinarians'))

@app.route('/veterinarians/delete/<int:vet_id>', methods=['POST'])
@login_required
@roles_required('Admin')
def delete_veterinarian(vet_id):
    try:
        # Check if veterinarian has existing appointments
        appt_count = query_db(
            "SELECT COUNT(*) AS total FROM appointments WHERE vet_id = %s",
            (vet_id,),
            one=True
        )['total']

        if appt_count > 0:
            flash(f'Cannot delete veterinarian: {appt_count} appointments are assigned to this doctor. Reassign or cancel them first.', 'warning')
            return redirect(url_for('veterinarians'))

        query_db("DELETE FROM veterinarians WHERE vet_id = %s", (vet_id,), commit=True)
        flash('Veterinarian removed successfully.', 'success')
    except Exception as e:
        flash(f'Error deleting veterinarian: {e}', 'danger')

    return redirect(url_for('veterinarians'))

# --------------------------------------------------------------------
# 6. Appointment Management
# --------------------------------------------------------------------

@app.route('/appointments')
@login_required
def appointments():
    date_filter = request.args.get('date', '').strip()
    status_filter = request.args.get('status', '').strip()
    vet_filter = request.args.get('vet_id', '').strip()
    search = request.args.get('search', '').strip()

    sql = """SELECT a.*, p.pet_name, p.species, o.name AS owner_name, o.phone AS owner_phone,
                    v.name AS vet_name, v.specialization,
                    t.treatment_id, b.bill_id, b.payment_status
             FROM appointments a
             JOIN pets p ON a.pet_id = p.pet_id
             JOIN pet_owners o ON p.owner_id = o.owner_id
             JOIN veterinarians v ON a.vet_id = v.vet_id
             LEFT JOIN treatments t ON a.appointment_id = t.appointment_id
             LEFT JOIN bills b ON a.appointment_id = b.appointment_id
             WHERE 1=1"""
    params = []

    if date_filter:
        sql += " AND a.appointment_date = %s"
        params.append(date_filter)
    if status_filter:
        sql += " AND a.status = %s"
        params.append(status_filter)
    if vet_filter:
        sql += " AND a.vet_id = %s"
        params.append(vet_filter)
    if search:
        sql += " AND (p.pet_name LIKE %s OR o.name LIKE %s OR a.reason LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    sql += " ORDER BY a.appointment_date DESC, a.appointment_time ASC"
    appointments_list = query_db(sql, tuple(params))

    # Reference lists for modals and filters
    all_pets = query_db("""SELECT p.pet_id, p.pet_name, p.species, o.name AS owner_name 
                           FROM pets p JOIN pet_owners o ON p.owner_id = o.owner_id 
                           ORDER BY p.pet_name ASC""")
    all_vets = query_db("SELECT vet_id, name, specialization FROM veterinarians ORDER BY name ASC")

    return render_template(
        'appointments.html',
        appointments=appointments_list,
        pets=all_pets,
        vets=all_vets,
        date_filter=date_filter,
        status_filter=status_filter,
        vet_filter=vet_filter,
        search=search
    )

@app.route('/appointments/book', methods=['POST'])
@login_required
@roles_required('Admin', 'Receptionist')
def book_appointment():
    pet_id = request.form.get('pet_id')
    vet_id = request.form.get('vet_id')
    appt_date = request.form.get('appointment_date')
    appt_time = request.form.get('appointment_time')
    reason = request.form.get('reason', '').strip()

    if not pet_id or not vet_id or not appt_date or not appt_time or not reason:
        flash('All appointment fields are required.', 'danger')
        return redirect(url_for('appointments'))

    # Double-booking collision detection check
    collision = query_db(
        """SELECT appointment_id FROM appointments 
           WHERE vet_id = %s AND appointment_date = %s AND appointment_time = %s AND status != 'Cancelled'""",
        (vet_id, appt_date, appt_time),
        one=True
    )

    if collision:
        vet = query_db("SELECT name FROM veterinarians WHERE vet_id = %s", (vet_id,), one=True)
        vet_name = vet['name'] if vet else 'Selected Doctor'
        flash(f'Double-Booking Conflict: {vet_name} is already booked on {appt_date} at {appt_time}. Please select another time or doctor.', 'danger')
        return redirect(url_for('appointments'))

    try:
        query_db(
            """INSERT INTO appointments (pet_id, vet_id, appointment_date, appointment_time, reason, status)
               VALUES (%s, %s, %s, %s, %s, 'Scheduled')""",
            (pet_id, vet_id, appt_date, appt_time, reason),
            commit=True
        )
        flash('Appointment booked successfully!', 'success')
    except Exception as e:
        flash(f'Error booking appointment: {e}', 'danger')

    return redirect(url_for('appointments'))

@app.route('/appointments/edit/<int:appointment_id>', methods=['POST'])
@login_required
@roles_required('Admin', 'Receptionist')
def edit_appointment(appointment_id):
    pet_id = request.form.get('pet_id')
    vet_id = request.form.get('vet_id')
    appt_date = request.form.get('appointment_date')
    appt_time = request.form.get('appointment_time')
    reason = request.form.get('reason', '').strip()
    status = request.form.get('status', 'Scheduled')

    # Double-booking check excluding this specific appointment
    if status != 'Cancelled':
        collision = query_db(
            """SELECT appointment_id FROM appointments 
               WHERE vet_id = %s AND appointment_date = %s AND appointment_time = %s 
                 AND status != 'Cancelled' AND appointment_id != %s""",
            (vet_id, appt_date, appt_time, appointment_id),
            one=True
        )
        if collision:
            flash(f'Conflict: The selected veterinarian is already booked for {appt_date} at {appt_time}.', 'danger')
            return redirect(url_for('appointments'))

    try:
        query_db(
            """UPDATE appointments 
               SET pet_id = %s, vet_id = %s, appointment_date = %s, 
                   appointment_time = %s, reason = %s, status = %s 
               WHERE appointment_id = %s""",
            (pet_id, vet_id, appt_date, appt_time, reason, status, appointment_id),
            commit=True
        )
        flash('Appointment updated successfully.', 'success')
    except Exception as e:
        flash(f'Error updating appointment: {e}', 'danger')

    return redirect(url_for('appointments'))

@app.route('/appointments/status/<int:appointment_id>', methods=['POST'])
@login_required
def change_appointment_status(appointment_id):
    status = request.form.get('status')
    if status in ['Scheduled', 'Completed', 'Cancelled']:
        query_db("UPDATE appointments SET status = %s WHERE appointment_id = %s", (status, appointment_id), commit=True)
        flash(f'Appointment status changed to {status}.', 'success')
    return redirect(request.referrer or url_for('appointments'))

# --------------------------------------------------------------------
# 7. Treatment Management
# --------------------------------------------------------------------

@app.route('/treatments')
@login_required
def treatments():
    treatments_list = query_db(
        """SELECT t.*, a.appointment_date, a.reason, p.pet_id, p.pet_name, p.species,
                  o.name AS owner_name, v.name AS vet_name,
                  COUNT(pr.prescription_id) AS prescription_count
           FROM treatments t
           JOIN appointments a ON t.appointment_id = a.appointment_id
           JOIN pets p ON a.pet_id = p.pet_id
           JOIN pet_owners o ON p.owner_id = o.owner_id
           JOIN veterinarians v ON a.vet_id = v.vet_id
           LEFT JOIN prescriptions pr ON t.treatment_id = pr.treatment_id
           GROUP BY t.treatment_id
           ORDER BY t.treatment_date DESC"""
    )

    # Completed or Scheduled appointments eligible for adding a treatment record
    eligible_appointments = query_db(
        """SELECT a.appointment_id, a.appointment_date, a.reason, p.pet_name, v.name AS vet_name
           FROM appointments a
           JOIN pets p ON a.pet_id = p.pet_id
           JOIN veterinarians v ON a.vet_id = v.vet_id
           LEFT JOIN treatments t ON a.appointment_id = t.appointment_id
           WHERE t.treatment_id IS NULL AND a.status != 'Cancelled'
           ORDER BY a.appointment_date DESC"""
    )

    return render_template(
        'treatments.html', 
        treatments=treatments_list, 
        eligible_appointments=eligible_appointments
    )

@app.route('/treatments/add', methods=['POST'])
@login_required
@roles_required('Admin', 'Veterinarian')
def add_treatment():
    appointment_id = request.form.get('appointment_id')
    diagnosis = request.form.get('diagnosis', '').strip()
    treatment_description = request.form.get('treatment_description', '').strip()
    treatment_date = request.form.get('treatment_date') or date.today().strftime('%Y-%m-%d')
    notes = request.form.get('notes', '').strip()

    if not appointment_id or not diagnosis or not treatment_description:
        flash('Appointment, diagnosis, and treatment description are required.', 'danger')
        return redirect(url_for('treatments'))

    # Atomic Transaction: Insert Treatment + Mark Appointment Completed + Create Bill if not present
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """INSERT INTO treatments (appointment_id, diagnosis, treatment_description, treatment_date, notes)
               VALUES (%s, %s, %s, %s, %s)""",
            (appointment_id, diagnosis, treatment_description, treatment_date, notes)
        )
        
        # Mark appointment as Completed
        cursor.execute(
            "UPDATE appointments SET status = 'Completed' WHERE appointment_id = %s",
            (appointment_id,)
        )

        # Check if bill exists, create default bill if not
        cursor.execute("SELECT bill_id FROM bills WHERE appointment_id = %s", (appointment_id,))
        bill = cursor.fetchone()
        if not bill:
            cursor.execute(
                """INSERT INTO bills (appointment_id, consultation_fee, treatment_fee, medicine_fee, vaccination_fee, total_amount, payment_status)
                   VALUES (%s, 50.00, 30.00, 0.00, 0.00, 80.00, 'Unpaid')""",
                (appointment_id,)
            )

        conn.commit()
        flash('Medical treatment recorded and appointment marked Completed. Invoice initialized.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Transaction failed while recording treatment: {e}', 'danger')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('treatments'))

# --------------------------------------------------------------------
# 8. Vaccination Management
# --------------------------------------------------------------------

@app.route('/vaccinations')
@login_required
def vaccinations():
    filter_type = request.args.get('filter', 'all')
    search = request.args.get('search', '').strip()

    sql = """SELECT v.*, p.pet_name, p.species, p.breed, o.name AS owner_name, o.phone AS owner_phone,
                    DATEDIFF(v.next_due_date, CURDATE()) AS days_difference,
                    CASE 
                        WHEN v.next_due_date < CURDATE() THEN 'OVERDUE'
                        WHEN v.next_due_date = CURDATE() THEN 'DUE TODAY'
                        WHEN v.next_due_date <= DATE_ADD(CURDATE(), INTERVAL 30 DAY) THEN 'UPCOMING'
                        ELSE 'CURRENT'
                    END AS alert_status
             FROM vaccinations v
             JOIN pets p ON v.pet_id = p.pet_id
             JOIN pet_owners o ON p.owner_id = o.owner_id
             WHERE 1=1"""
    params = []

    if filter_type == 'upcoming':
        sql += " AND v.next_due_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)"
    elif filter_type == 'overdue':
        sql += " AND v.next_due_date < CURDATE()"

    if search:
        sql += " AND (p.pet_name LIKE %s OR v.vaccine_name LIKE %s OR o.name LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    sql += " ORDER BY v.next_due_date ASC"
    vaccinations_list = query_db(sql, tuple(params))

    all_pets = query_db("""SELECT p.pet_id, p.pet_name, p.species, o.name AS owner_name 
                           FROM pets p JOIN pet_owners o ON p.owner_id = o.owner_id 
                           ORDER BY p.pet_name ASC""")

    return render_template(
        'vaccinations.html',
        vaccinations=vaccinations_list,
        pets=all_pets,
        filter_type=filter_type,
        search=search
    )

@app.route('/vaccinations/add', methods=['POST'])
@login_required
@roles_required('Admin', 'Veterinarian')
def add_vaccination():
    pet_id = request.form.get('pet_id')
    vaccine_name = request.form.get('vaccine_name', '').strip()
    vax_date = request.form.get('vaccination_date') or date.today().strftime('%Y-%m-%d')
    next_due = request.form.get('next_due_date') or None
    notes = request.form.get('notes', '').strip()

    if not pet_id or not vaccine_name or not vax_date:
        flash('Pet, Vaccine Name, and Vaccination Date are required.', 'danger')
        return redirect(url_for('vaccinations'))

    try:
        query_db(
            """INSERT INTO vaccinations (pet_id, vaccine_name, vaccination_date, next_due_date, notes)
               VALUES (%s, %s, %s, %s, %s)""",
            (pet_id, vaccine_name, vax_date, next_due, notes),
            commit=True
        )
        flash(f'Vaccination "{vaccine_name}" recorded successfully.', 'success')
    except Exception as e:
        flash(f'Error adding vaccination: {e}', 'danger')

    return redirect(url_for('vaccinations'))

@app.route('/vaccinations/delete/<int:vaccination_id>', methods=['POST'])
@login_required
@roles_required('Admin')
def delete_vaccination(vaccination_id):
    try:
        query_db("DELETE FROM vaccinations WHERE vaccination_id = %s", (vaccination_id,), commit=True)
        flash('Vaccination record removed.', 'success')
    except Exception as e:
        flash(f'Error deleting vaccination: {e}', 'danger')
    return redirect(url_for('vaccinations'))

# --------------------------------------------------------------------
# 9. Prescription Management
# --------------------------------------------------------------------

@app.route('/prescriptions')
@login_required
def prescriptions():
    prescriptions_list = query_db(
        """SELECT pr.*, t.diagnosis, t.treatment_date, p.pet_name, p.species, o.name AS owner_name, v.name AS vet_name
           FROM prescriptions pr
           JOIN treatments t ON pr.treatment_id = t.treatment_id
           JOIN appointments a ON t.appointment_id = a.appointment_id
           JOIN pets p ON a.pet_id = p.pet_id
           JOIN pet_owners o ON p.owner_id = o.owner_id
           JOIN veterinarians v ON a.vet_id = v.vet_id
           ORDER BY pr.prescription_id DESC"""
    )

    treatments_list = query_db(
        """SELECT t.treatment_id, t.diagnosis, t.treatment_date, p.pet_name 
           FROM treatments t
           JOIN appointments a ON t.appointment_id = a.appointment_id
           JOIN pets p ON a.pet_id = p.pet_id
           ORDER BY t.treatment_date DESC"""
    )

    return render_template(
        'prescriptions.html',
        prescriptions=prescriptions_list,
        treatments=treatments_list
    )

@app.route('/prescriptions/add', methods=['POST'])
@login_required
@roles_required('Admin', 'Veterinarian')
def add_prescription():
    treatment_id = request.form.get('treatment_id')
    medicine_name = request.form.get('medicine_name', '').strip()
    dosage = request.form.get('dosage', '').strip()
    frequency = request.form.get('frequency', '').strip()
    duration = request.form.get('duration', '').strip()
    instructions = request.form.get('instructions', '').strip()

    if not treatment_id or not medicine_name or not dosage or not frequency or not duration:
        flash('Please fill in all mandatory prescription fields.', 'danger')
        return redirect(url_for('prescriptions'))

    try:
        query_db(
            """INSERT INTO prescriptions (treatment_id, medicine_name, dosage, frequency, duration, instructions)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (treatment_id, medicine_name, dosage, frequency, duration, instructions),
            commit=True
        )
        flash(f'Prescription for "{medicine_name}" added successfully.', 'success')
    except Exception as e:
        flash(f'Error adding prescription: {e}', 'danger')

    return redirect(url_for('prescriptions'))

@app.route('/prescriptions/delete/<int:prescription_id>', methods=['POST'])
@login_required
@roles_required('Admin', 'Veterinarian')
def delete_prescription(prescription_id):
    try:
        query_db("DELETE FROM prescriptions WHERE prescription_id = %s", (prescription_id,), commit=True)
        flash('Prescription item removed.', 'success')
    except Exception as e:
        flash(f'Error deleting prescription: {e}', 'danger')
    return redirect(url_for('prescriptions'))

# --------------------------------------------------------------------
# 10. Billing and Invoicing
# --------------------------------------------------------------------

@app.route('/billing')
@login_required
def billing():
    status_filter = request.args.get('status', 'all')
    search = request.args.get('search', '').strip()

    sql = """SELECT b.*, a.appointment_date, p.pet_name, p.species, o.name AS owner_name, o.phone AS owner_phone, v.name AS vet_name
             FROM bills b
             JOIN appointments a ON b.appointment_id = a.appointment_id
             JOIN pets p ON a.pet_id = p.pet_id
             JOIN pet_owners o ON p.owner_id = o.owner_id
             JOIN veterinarians v ON a.vet_id = v.vet_id
             WHERE 1=1"""
    params = []

    if status_filter in ['Paid', 'Unpaid']:
        sql += " AND b.payment_status = %s"
        params.append(status_filter)

    if search:
        sql += " AND (p.pet_name LIKE %s OR o.name LIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])

    sql += " ORDER BY b.bill_id DESC"
    bills_list = query_db(sql, tuple(params))

    # Appointments that do not have an invoice generated yet
    unbilled_appointments = query_db(
        """SELECT a.appointment_id, a.appointment_date, p.pet_name, o.name AS owner_name
           FROM appointments a
           JOIN pets p ON a.pet_id = p.pet_id
           JOIN pet_owners o ON p.owner_id = o.owner_id
           LEFT JOIN bills b ON a.appointment_id = b.appointment_id
           WHERE b.bill_id IS NULL AND a.status != 'Cancelled'
           ORDER BY a.appointment_date DESC"""
    )

    # Billing KPI Totals
    kpi = query_db(
        """SELECT 
               COUNT(*) AS total_invoices,
               COALESCE(SUM(total_amount), 0) AS gross_total,
               COALESCE(SUM(CASE WHEN payment_status = 'Paid' THEN total_amount ELSE 0 END), 0) AS total_collected,
               COALESCE(SUM(CASE WHEN payment_status = 'Unpaid' THEN total_amount ELSE 0 END), 0) AS total_unpaid
           FROM bills""",
        one=True
    )

    return render_template(
        'billing.html',
        bills=bills_list,
        unbilled_appointments=unbilled_appointments,
        kpi=kpi,
        status_filter=status_filter,
        search=search
    )

@app.route('/billing/generate', methods=['POST'])
@login_required
@roles_required('Admin', 'Receptionist')
def generate_bill():
    appointment_id = request.form.get('appointment_id')
    consultation = float(request.form.get('consultation_fee') or 0.0)
    treatment = float(request.form.get('treatment_fee') or 0.0)
    medicine = float(request.form.get('medicine_fee') or 0.0)
    vaccination = float(request.form.get('vaccination_fee') or 0.0)
    payment_status = request.form.get('payment_status', 'Unpaid')
    payment_date = date.today().strftime('%Y-%m-%d') if payment_status == 'Paid' else None

    total_amount = consultation + treatment + medicine + vaccination

    try:
        query_db(
            """INSERT INTO bills (appointment_id, consultation_fee, treatment_fee, medicine_fee, vaccination_fee, total_amount, payment_status, payment_date)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (appointment_id, consultation, treatment, medicine, vaccination, total_amount, payment_status, payment_date),
            commit=True
        )
        flash(f'Invoice generated for ₹/USD {total_amount:.2f} successfully.', 'success')
    except Exception as e:
        flash(f'Error generating bill: {e}', 'danger')

    return redirect(url_for('billing'))

@app.route('/billing/pay/<int:bill_id>', methods=['POST'])
@login_required
@roles_required('Admin', 'Receptionist')
def pay_bill(bill_id):
    try:
        query_db(
            "UPDATE bills SET payment_status = 'Paid', payment_date = CURDATE() WHERE bill_id = %s",
            (bill_id,),
            commit=True
        )
        flash('Bill marked as Paid successfully.', 'success')
    except Exception as e:
        flash(f'Error updating bill payment: {e}', 'danger')
    return redirect(url_for('billing'))

@app.route('/billing/edit/<int:bill_id>', methods=['POST'])
@login_required
@roles_required('Admin', 'Receptionist')
def edit_bill(bill_id):
    consultation = float(request.form.get('consultation_fee') or 0.0)
    treatment = float(request.form.get('treatment_fee') or 0.0)
    medicine = float(request.form.get('medicine_fee') or 0.0)
    vaccination = float(request.form.get('vaccination_fee') or 0.0)
    payment_status = request.form.get('payment_status', 'Unpaid')
    payment_date = request.form.get('payment_date') or (date.today().strftime('%Y-%m-%d') if payment_status == 'Paid' else None)

    total_amount = consultation + treatment + medicine + vaccination

    try:
        query_db(
            """UPDATE bills 
               SET consultation_fee = %s, treatment_fee = %s, medicine_fee = %s, 
                   vaccination_fee = %s, total_amount = %s, payment_status = %s, payment_date = %s
               WHERE bill_id = %s""",
            (consultation, treatment, medicine, vaccination, total_amount, payment_status, payment_date, bill_id),
            commit=True
        )
        flash('Invoice recalculated and updated successfully.', 'success')
    except Exception as e:
        flash(f'Error updating invoice: {e}', 'danger')

    return redirect(url_for('billing'))

# --------------------------------------------------------------------
# 11. Reports (Computed using SQL queries)
# --------------------------------------------------------------------

@app.route('/reports')
@login_required
def reports():
    try:
        # Report 1: Number of pets by species (SQL GROUP BY)
        species_report = query_db(
            """SELECT species, COUNT(*) AS pet_count, ROUND(AVG(weight), 2) AS avg_weight 
               FROM pets 
               GROUP BY species 
               ORDER BY pet_count DESC"""
        )

        # Report 2: Number of appointments by veterinarian (SQL JOIN + GROUP BY)
        vet_report = query_db(
            """SELECT v.name AS vet_name, v.specialization,
                      COUNT(a.appointment_id) AS total_appointments,
                      SUM(CASE WHEN a.status = 'Completed' THEN 1 ELSE 0 END) AS completed_appointments,
                      COALESCE(SUM(b.total_amount), 0) AS total_revenue
               FROM veterinarians v
               LEFT JOIN appointments a ON v.vet_id = a.vet_id
               LEFT JOIN bills b ON a.appointment_id = b.appointment_id
               GROUP BY v.vet_id, v.name, v.specialization
               ORDER BY total_revenue DESC"""
        )

        # Report 3: Monthly Revenue Realization (SQL DATE_FORMAT + SUM)
        monthly_revenue = query_db(
            """SELECT DATE_FORMAT(payment_date, '%Y-%m') AS month_label,
                      COUNT(bill_id) AS paid_bills_count,
                      SUM(total_amount) AS revenue_amount
               FROM bills
               WHERE payment_status = 'Paid' AND payment_date IS NOT NULL
               GROUP BY DATE_FORMAT(payment_date, '%Y-%m')
               ORDER BY month_label DESC"""
        )

        # Report 4: Pending / Unpaid Bills (SQL WHERE + JOIN)
        unpaid_bills = query_db(
            """SELECT b.bill_id, b.total_amount, a.appointment_date,
                      p.pet_name, o.name AS owner_name, o.phone AS owner_phone
               FROM bills b
               JOIN appointments a ON b.appointment_id = a.appointment_id
               JOIN pets p ON a.pet_id = p.pet_id
               JOIN pet_owners o ON p.owner_id = o.owner_id
               WHERE b.payment_status = 'Unpaid'
               ORDER BY a.appointment_date ASC"""
        )

        # Report 5: Upcoming Vaccinations (SQL View query)
        upcoming_vax = query_db(
            """SELECT * FROM view_upcoming_vaccinations 
               WHERE days_until_due <= 30
               ORDER BY next_due_date ASC"""
        )

        # Report 6: Appointment Status Distribution (SQL COUNT + GROUP BY)
        status_report = query_db(
            """SELECT status, COUNT(*) AS count 
               FROM appointments 
               GROUP BY status"""
        )

        return render_template(
            'reports.html',
            species_report=species_report,
            vet_report=vet_report,
            monthly_revenue=monthly_revenue,
            unpaid_bills=unpaid_bills,
            upcoming_vax=upcoming_vax,
            status_report=status_report
        )
    except Exception as e:
        flash(f'Error compiling SQL reports: {e}', 'danger')
        return render_template('reports.html')

if __name__ == '__main__':
    # Run development server
    print("\n* PetCare+ — Smart Pet Clinic Management System")
    print("* Running on http://127.0.0.1:5000\n")
    app.run(debug=True, port=5000)
