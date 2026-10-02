-- ====================================================================
-- PetCare+ — Smart Pet Clinic Management System
-- Database Schema Script
-- DBMS Project - College CSE Department
-- ====================================================================

-- 1. Create and Select Database
CREATE DATABASE IF NOT EXISTS petcare_db;
USE petcare_db;

-- 2. Drop existing views and tables if rebuilding (in reverse FK order)
DROP VIEW IF EXISTS view_upcoming_vaccinations;
DROP VIEW IF EXISTS view_billing_summary;
DROP VIEW IF EXISTS view_appointment_details;
DROP VIEW IF EXISTS view_pet_details;

DROP TABLE IF EXISTS bills;
DROP TABLE IF EXISTS prescriptions;
DROP TABLE IF EXISTS vaccinations;
DROP TABLE IF EXISTS treatments;
DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS veterinarians;
DROP TABLE IF EXISTS pets;
DROP TABLE IF EXISTS pet_owners;
DROP TABLE IF EXISTS users;

-- ====================================================================
-- 3. Core Relational Tables
-- ====================================================================

-- Table 1: users (Authentication and Role-based Access)
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('Admin', 'Receptionist', 'Veterinarian') NOT NULL DEFAULT 'Receptionist',
    full_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Table 2: pet_owners (Owner Information)
CREATE TABLE pet_owners (
    owner_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    address VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Table 3: pets (Pet Patients, linked to Owner)
CREATE TABLE pets (
    pet_id INT AUTO_INCREMENT PRIMARY KEY,
    owner_id INT NOT NULL,
    pet_name VARCHAR(100) NOT NULL,
    species VARCHAR(50) NOT NULL,
    breed VARCHAR(50) DEFAULT 'Unknown',
    gender ENUM('Male', 'Female', 'Unknown') DEFAULT 'Unknown',
    date_of_birth DATE,
    weight DECIMAL(5,2) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_pets_owner 
        FOREIGN KEY (owner_id) REFERENCES pet_owners(owner_id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_pet_weight CHECK (weight IS NULL OR weight > 0)
) ENGINE=InnoDB;

-- Table 4: veterinarians (Clinic Doctors)
CREATE TABLE veterinarians (
    vet_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    specialization VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Table 5: appointments (Clinic Bookings)
CREATE TABLE appointments (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,
    pet_id INT NOT NULL,
    vet_id INT NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    reason VARCHAR(255) NOT NULL,
    status ENUM('Scheduled', 'Completed', 'Cancelled') NOT NULL DEFAULT 'Scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_appointments_pet 
        FOREIGN KEY (pet_id) REFERENCES pets(pet_id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_appointments_vet 
        FOREIGN KEY (vet_id) REFERENCES veterinarians(vet_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Table 6: treatments (Medical Records for Appointments)
CREATE TABLE treatments (
    treatment_id INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id INT NOT NULL UNIQUE,
    diagnosis VARCHAR(255) NOT NULL,
    treatment_description TEXT NOT NULL,
    treatment_date DATE NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_treatments_appointment 
        FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Table 7: vaccinations (Preventive Care Tracking)
CREATE TABLE vaccinations (
    vaccination_id INT AUTO_INCREMENT PRIMARY KEY,
    pet_id INT NOT NULL,
    vaccine_name VARCHAR(100) NOT NULL,
    vaccination_date DATE NOT NULL,
    next_due_date DATE DEFAULT NULL,
    notes VARCHAR(255) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_vaccinations_pet 
        FOREIGN KEY (pet_id) REFERENCES pets(pet_id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_vaccination_dates 
        CHECK (next_due_date IS NULL OR next_due_date >= vaccination_date)
) ENGINE=InnoDB;

-- Table 8: prescriptions (Medications linked to Treatments)
CREATE TABLE prescriptions (
    prescription_id INT AUTO_INCREMENT PRIMARY KEY,
    treatment_id INT NOT NULL,
    medicine_name VARCHAR(100) NOT NULL,
    dosage VARCHAR(100) NOT NULL,
    frequency VARCHAR(100) NOT NULL,
    duration VARCHAR(100) NOT NULL,
    instructions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_prescriptions_treatment 
        FOREIGN KEY (treatment_id) REFERENCES treatments(treatment_id) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Table 9: bills (Invoicing and Financials)
CREATE TABLE bills (
    bill_id INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id INT NOT NULL UNIQUE,
    consultation_fee DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    treatment_fee DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    medicine_fee DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    vaccination_fee DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total_amount DECIMAL(10,2) NOT NULL,
    payment_status ENUM('Unpaid', 'Paid') NOT NULL DEFAULT 'Unpaid',
    payment_date DATE DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_bills_appointment 
        FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_fees_positive CHECK (
        consultation_fee >= 0 AND 
        treatment_fee >= 0 AND 
        medicine_fee >= 0 AND 
        vaccination_fee >= 0 AND 
        total_amount >= 0
    )
) ENGINE=InnoDB;

-- ====================================================================
-- 4. Useful Performance Indexes
-- ====================================================================
CREATE INDEX idx_appointments_date_vet ON appointments(appointment_date, vet_id);
CREATE INDEX idx_pets_species ON pets(species);
CREATE INDEX idx_bills_status ON bills(payment_status);
CREATE INDEX idx_vaccinations_due ON vaccinations(next_due_date);

-- ====================================================================
-- 5. Database Views (for simplified joins and clean reporting)
-- ====================================================================

-- View 1: Complete Appointment Details
CREATE VIEW view_appointment_details AS
SELECT 
    a.appointment_id,
    a.appointment_date,
    a.appointment_time,
    a.reason,
    a.status,
    a.created_at,
    p.pet_id,
    p.pet_name,
    p.species,
    p.breed,
    o.owner_id,
    o.name AS owner_name,
    o.phone AS owner_phone,
    v.vet_id,
    v.name AS vet_name,
    v.specialization
FROM appointments a
JOIN pets p ON a.pet_id = p.pet_id
JOIN pet_owners o ON p.owner_id = o.owner_id
JOIN veterinarians v ON a.vet_id = v.vet_id;

-- View 2: Complete Billing Summary
CREATE VIEW view_billing_summary AS
SELECT 
    b.bill_id,
    b.appointment_id,
    b.consultation_fee,
    b.treatment_fee,
    b.medicine_fee,
    b.vaccination_fee,
    b.total_amount,
    b.payment_status,
    b.payment_date,
    b.created_at AS bill_created_at,
    a.appointment_date,
    p.pet_name,
    p.species,
    o.name AS owner_name,
    o.phone AS owner_phone,
    v.name AS vet_name
FROM bills b
JOIN appointments a ON b.appointment_id = a.appointment_id
JOIN pets p ON a.pet_id = p.pet_id
JOIN pet_owners o ON p.owner_id = o.owner_id
JOIN veterinarians v ON a.vet_id = v.vet_id;

-- View 3: Upcoming and Overdue Vaccinations
CREATE VIEW view_upcoming_vaccinations AS
SELECT 
    v.vaccination_id,
    v.vaccine_name,
    v.vaccination_date,
    v.next_due_date,
    v.notes,
    p.pet_id,
    p.pet_name,
    p.species,
    p.breed,
    o.owner_id,
    o.name AS owner_name,
    o.phone AS owner_phone,
    o.email AS owner_email,
    DATEDIFF(v.next_due_date, CURDATE()) AS days_until_due
FROM vaccinations v
JOIN pets p ON v.pet_id = p.pet_id
JOIN pet_owners o ON p.owner_id = o.owner_id
WHERE v.next_due_date IS NOT NULL;

-- View 4: Comprehensive Pet Overview
CREATE VIEW view_pet_details AS
SELECT 
    p.pet_id,
    p.pet_name,
    p.species,
    p.breed,
    p.gender,
    p.date_of_birth,
    p.weight,
    o.owner_id,
    o.name AS owner_name,
    o.phone AS owner_phone,
    COUNT(DISTINCT a.appointment_id) AS total_appointments,
    COUNT(DISTINCT vc.vaccination_id) AS total_vaccinations
FROM pets p
JOIN pet_owners o ON p.owner_id = o.owner_id
LEFT JOIN appointments a ON p.pet_id = a.pet_id
LEFT JOIN vaccinations vc ON p.pet_id = vc.pet_id
GROUP BY p.pet_id, p.pet_name, p.species, p.breed, p.gender, p.date_of_birth, p.weight, o.owner_id, o.name, o.phone;
