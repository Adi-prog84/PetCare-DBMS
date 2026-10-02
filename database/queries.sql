-- ====================================================================
-- PetCare+ — Smart Pet Clinic Management System
-- Demonstration SQL Queries
-- Designed for DBMS Course Evaluation and Viva Demonstration
-- ====================================================================

USE petcare_db;

-- --------------------------------------------------------------------
-- QUERY 1: Basic SELECT with Multiple Filtering Conditions (WHERE & AND)
-- Purpose: Retrieve all dogs weighing more than 20 kg
-- Concepts: SELECT, WHERE, Relational Operators, AND
-- --------------------------------------------------------------------
SELECT pet_id, pet_name, species, breed, weight 
FROM pets 
WHERE species = 'Dog' AND weight > 20.00
ORDER BY weight DESC;

-- --------------------------------------------------------------------
-- QUERY 2: Multi-Column Sorting (ORDER BY)
-- Purpose: List all veterinarians ordered alphabetically by specialization, then name
-- Concepts: ORDER BY with multiple columns, ASC/DESC
-- --------------------------------------------------------------------
SELECT vet_id, name, specialization, phone, email
FROM veterinarians
ORDER BY specialization ASC, name ASC;

-- --------------------------------------------------------------------
-- QUERY 3: 3-Table INNER JOIN
-- Purpose: Display all appointments with Pet name, Owner name, and Vet name
-- Concepts: INNER JOIN across 3 relational tables
-- --------------------------------------------------------------------
SELECT 
    a.appointment_id,
    a.appointment_date,
    a.appointment_time,
    p.pet_name,
    p.species,
    o.name AS owner_name,
    o.phone AS owner_phone,
    v.name AS doctor_name,
    a.status
FROM appointments a
INNER JOIN pets p ON a.pet_id = p.pet_id
INNER JOIN pet_owners o ON p.owner_id = o.owner_id
INNER JOIN veterinarians v ON a.vet_id = v.vet_id
ORDER BY a.appointment_date DESC, a.appointment_time DESC;

-- --------------------------------------------------------------------
-- QUERY 4: 5-Table Deep Relational JOIN
-- Purpose: Generate a complete medical examination record with owner, pet, vet, treatment, and prescription
-- Concepts: Complex multi-table JOINs, NULL handling with LEFT JOIN
-- --------------------------------------------------------------------
SELECT 
    a.appointment_id,
    p.pet_name,
    o.name AS owner_name,
    v.name AS attending_vet,
    t.diagnosis,
    t.treatment_description,
    pr.medicine_name,
    pr.dosage,
    pr.frequency,
    pr.duration
FROM appointments a
JOIN pets p ON a.pet_id = p.pet_id
JOIN pet_owners o ON p.owner_id = o.owner_id
JOIN veterinarians v ON a.vet_id = v.vet_id
JOIN treatments t ON a.appointment_id = t.appointment_id
LEFT JOIN prescriptions pr ON t.treatment_id = pr.treatment_id
ORDER BY a.appointment_id, pr.prescription_id;

-- --------------------------------------------------------------------
-- QUERY 5: LEFT OUTER JOIN
-- Purpose: Identify all pets that have never received any vaccinations
-- Concepts: LEFT JOIN, IS NULL filter (Antijoin pattern)
-- --------------------------------------------------------------------
SELECT 
    p.pet_id,
    p.pet_name,
    p.species,
    o.name AS owner_name,
    o.phone AS owner_phone
FROM pets p
JOIN pet_owners o ON p.owner_id = o.owner_id
LEFT JOIN vaccinations v ON p.pet_id = v.pet_id
WHERE v.vaccination_id IS NULL;

-- --------------------------------------------------------------------
-- QUERY 6: Aggregate Functions
-- Purpose: Calculate clinic financial summary (Total, Average, Min, Max, Count)
-- Concepts: SUM, AVG, MIN, MAX, COUNT
-- --------------------------------------------------------------------
SELECT 
    COUNT(*) AS total_bills_generated,
    SUM(total_amount) AS gross_revenue_invoiced,
    AVG(total_amount) AS average_bill_amount,
    MIN(total_amount) AS minimum_bill_amount,
    MAX(total_amount) AS maximum_bill_amount,
    SUM(consultation_fee) AS total_consultation_revenue,
    SUM(treatment_fee) AS total_treatment_revenue,
    SUM(medicine_fee) AS total_medicine_revenue
FROM bills;

-- --------------------------------------------------------------------
-- QUERY 7: GROUP BY with Aggregate Function
-- Purpose: Count the number of pets categorized by species
-- Concepts: GROUP BY, COUNT(*), Aliasing
-- --------------------------------------------------------------------
SELECT 
    species, 
    COUNT(*) AS total_registered,
    ROUND(AVG(weight), 2) AS average_weight_kg
FROM pets
GROUP BY species
ORDER BY total_registered DESC;

-- --------------------------------------------------------------------
-- QUERY 8: GROUP BY with HAVING Clause
-- Purpose: Find veterinarians who have handled 2 or more completed appointments
-- Concepts: GROUP BY, HAVING (filters aggregated groups, distinct from WHERE)
-- --------------------------------------------------------------------
SELECT 
    v.vet_id,
    v.name AS veterinarian_name,
    v.specialization,
    COUNT(a.appointment_id) AS completed_appointments_count
FROM veterinarians v
JOIN appointments a ON v.vet_id = a.vet_id
WHERE a.status = 'Completed'
GROUP BY v.vet_id, v.name, v.specialization
HAVING COUNT(a.appointment_id) >= 2
ORDER BY completed_appointments_count DESC;

-- --------------------------------------------------------------------
-- QUERY 9: Subquery in WHERE Clause using NOT IN
-- Purpose: Find owners who currently do NOT have any active appointments scheduled
-- Concepts: Subquery, NOT IN
-- --------------------------------------------------------------------
SELECT owner_id, name, phone, email
FROM pet_owners
WHERE owner_id NOT IN (
    SELECT DISTINCT p.owner_id
    FROM pets p
    JOIN appointments a ON p.pet_id = a.pet_id
    WHERE a.status = 'Scheduled'
);

-- --------------------------------------------------------------------
-- QUERY 10: Subquery with IN Operator
-- Purpose: Identify pet owners who have unpaid invoices
-- Concepts: Subquery, IN operator, table joins inside subquery
-- --------------------------------------------------------------------
SELECT owner_id, name, phone, email 
FROM pet_owners
WHERE owner_id IN (
    SELECT p.owner_id
    FROM pets p
    JOIN appointments a ON p.pet_id = a.pet_id
    JOIN bills b ON a.appointment_id = b.appointment_id
    WHERE b.payment_status = 'Unpaid'
);

-- --------------------------------------------------------------------
-- QUERY 11: Correlated Subquery
-- Purpose: Find pets whose weight is above the average weight for their species
-- Concepts: Correlated Subquery (inner query references outer query attribute)
-- --------------------------------------------------------------------
SELECT p1.pet_id, p1.pet_name, p1.species, p1.breed, p1.weight
FROM pets p1
WHERE p1.weight > (
    SELECT AVG(p2.weight)
    FROM pets p2
    WHERE p2.species = p1.species
)
ORDER BY p1.species, p1.weight DESC;

-- --------------------------------------------------------------------
-- QUERY 12: Date-based Filtering (Today and Upcoming Appointments)
-- Purpose: Retrieve appointments scheduled for today or within the next 7 days
-- Concepts: CURDATE(), INTERVAL arithmetic, DATE comparison
-- --------------------------------------------------------------------
SELECT 
    a.appointment_id,
    a.appointment_date,
    a.appointment_time,
    p.pet_name,
    v.name AS vet_name,
    a.reason
FROM appointments a
JOIN pets p ON a.pet_id = p.pet_id
JOIN veterinarians v ON a.vet_id = v.vet_id
WHERE a.appointment_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY)
  AND a.status = 'Scheduled'
ORDER BY a.appointment_date ASC, a.appointment_time ASC;

-- --------------------------------------------------------------------
-- QUERY 13: Vaccination Alert Query (Upcoming or Overdue)
-- Purpose: Detect vaccinations due within 30 days or already overdue
-- Concepts: DATEDIFF, CASE Expression, Alert Status Categorization
-- --------------------------------------------------------------------
SELECT 
    v.vaccination_id,
    p.pet_name,
    p.species,
    o.name AS owner_name,
    o.phone AS owner_phone,
    v.vaccine_name,
    v.next_due_date,
    DATEDIFF(v.next_due_date, CURDATE()) AS days_difference,
    CASE 
        WHEN v.next_due_date < CURDATE() THEN 'OVERDUE'
        WHEN v.next_due_date = CURDATE() THEN 'DUE TODAY'
        ELSE 'UPCOMING'
    END AS alert_status
FROM vaccinations v
JOIN pets p ON v.pet_id = p.pet_id
JOIN pet_owners o ON p.owner_id = o.owner_id
WHERE v.next_due_date <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)
ORDER BY v.next_due_date ASC;

-- --------------------------------------------------------------------
-- QUERY 14: Double-Booking Prevention Query (Collision Detection)
-- Purpose: Query used by the backend to detect if a vet already has an appointment
-- Concepts: Concurrency safeguard, exact datetime matching
-- --------------------------------------------------------------------
SELECT appointment_id, pet_id, reason
FROM appointments
WHERE vet_id = 1 
  AND appointment_date = '2026-09-28' 
  AND appointment_time = '10:00:00'
  AND status != 'Cancelled';

-- --------------------------------------------------------------------
-- QUERY 15: Monthly Revenue Breakdown
-- Purpose: Aggregate realized income by year and month
-- Concepts: DATE_FORMAT, SUM, conditional aggregation
-- --------------------------------------------------------------------
SELECT 
    DATE_FORMAT(payment_date, '%Y-%m') AS revenue_month,
    COUNT(bill_id) AS total_bills_paid,
    SUM(total_amount) AS total_revenue_collected
FROM bills
WHERE payment_status = 'Paid' AND payment_date IS NOT NULL
GROUP BY DATE_FORMAT(payment_date, '%Y-%m')
ORDER BY revenue_month DESC;

-- --------------------------------------------------------------------
-- QUERY 16: Top Revenue-Generating Veterinarians
-- Purpose: Rank veterinarians by total billing generated from their completed visits
-- Concepts: SUM, JOIN, GROUP BY, ORDER BY DESC
-- --------------------------------------------------------------------
SELECT 
    v.vet_id,
    v.name AS vet_name,
    v.specialization,
    COUNT(b.bill_id) AS total_invoices,
    SUM(b.total_amount) AS total_revenue_generated
FROM veterinarians v
JOIN appointments a ON v.vet_id = a.vet_id
JOIN bills b ON a.appointment_id = b.appointment_id
GROUP BY v.vet_id, v.name, v.specialization
ORDER BY total_revenue_generated DESC;

-- --------------------------------------------------------------------
-- QUERY 17: Querying from Database View (view_appointment_details)
-- Purpose: Retrieve full appointment details using an abstract database view
-- Concepts: Database View abstraction, simplification of client queries
-- --------------------------------------------------------------------
SELECT * 
FROM view_appointment_details
WHERE status = 'Scheduled'
ORDER BY appointment_date ASC, appointment_time ASC;

-- --------------------------------------------------------------------
-- QUERY 18: Querying from Database View (view_billing_summary)
-- Purpose: Retrieve all unpaid bills using the billing summary view
-- Concepts: View utilization, WHERE filter on view
-- --------------------------------------------------------------------
SELECT 
    bill_id,
    appointment_id,
    pet_name,
    owner_name,
    owner_phone,
    total_amount,
    payment_status
FROM view_billing_summary
WHERE payment_status = 'Unpaid';

-- --------------------------------------------------------------------
-- QUERY 19: Querying from Database View (view_pet_details)
-- Purpose: Get pet statistics with total visits and vaccinations
-- Concepts: Aggregated View query
-- --------------------------------------------------------------------
SELECT 
    pet_name,
    species,
    owner_name,
    total_appointments,
    total_vaccinations
FROM view_pet_details
ORDER BY total_appointments DESC;

-- --------------------------------------------------------------------
-- QUERY 20: Comprehensive Medical Dossier for a Specific Pet
-- Purpose: Fetch chronological treatments and diagnoses for Pet ID 1 (Max)
-- Concepts: Targeted filtering, relational integrity
-- --------------------------------------------------------------------
SELECT 
    a.appointment_date,
    v.name AS attending_vet,
    t.diagnosis,
    t.treatment_description,
    t.notes
FROM treatments t
JOIN appointments a ON t.appointment_id = a.appointment_id
JOIN veterinarians v ON a.vet_id = v.vet_id
WHERE a.pet_id = 1
ORDER BY a.appointment_date DESC;

-- --------------------------------------------------------------------
-- QUERY 21: UPDATE Operation (Marking Bill as Paid)
-- Purpose: Update invoice status and set payment date to current date
-- Concepts: UPDATE, SET, WHERE condition
-- --------------------------------------------------------------------
UPDATE bills
SET payment_status = 'Paid',
    payment_date = CURDATE()
WHERE bill_id = 4 AND payment_status = 'Unpaid';

-- --------------------------------------------------------------------
-- QUERY 22: UPDATE Operation with Calculation
-- Purpose: Re-calculate total bill amount dynamically based on component fees
-- Concepts: UPDATE with arithmetic expression
-- --------------------------------------------------------------------
UPDATE bills
SET total_amount = consultation_fee + treatment_fee + medicine_fee + vaccination_fee
WHERE bill_id = 7;

-- --------------------------------------------------------------------
-- QUERY 23: INSERT Operation (Recording a New Vaccination)
-- Purpose: Add a new vaccination booster with parameterized next due date
-- Concepts: INSERT INTO ... VALUES
-- --------------------------------------------------------------------
INSERT INTO vaccinations (pet_id, vaccine_name, vaccination_date, next_due_date, notes)
VALUES (4, 'FVRCP Booster', CURDATE(), DATE_ADD(CURDATE(), INTERVAL 1 YEAR), 'Annual routine kitten booster');

-- --------------------------------------------------------------------
-- QUERY 24: Appointment Status Distribution Report
-- Purpose: Breakdown of appointments by status with percentages
-- Concepts: CASE statement inside SUM, conditional counts
-- --------------------------------------------------------------------
SELECT 
    COUNT(*) AS total_appointments,
    SUM(CASE WHEN status = 'Scheduled' THEN 1 ELSE 0 END) AS scheduled_count,
    SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) AS completed_count,
    SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_count
FROM appointments;

-- --------------------------------------------------------------------
-- QUERY 25: Relational Transaction Simulation (ACID demonstration)
-- Purpose: Atomically record treatment and update appointment status to 'Completed'
-- Concepts: START TRANSACTION, COMMIT, ROLLBACK, ACID properties
-- --------------------------------------------------------------------
START TRANSACTION;

-- Step 1: Update appointment status
UPDATE appointments 
SET status = 'Completed' 
WHERE appointment_id = 9;

-- Step 2: Insert treatment record
INSERT INTO treatments (appointment_id, diagnosis, treatment_description, treatment_date, notes)
VALUES (9, 'Healthy Kitten Exam', 'General physical checkup, clear vitals, temperature normal.', CURDATE(), 'Grow chart tracking well.');

-- Step 3: Insert initial billing record
INSERT INTO bills (appointment_id, consultation_fee, treatment_fee, medicine_fee, vaccination_fee, total_amount, payment_status, payment_date)
VALUES (9, 50.00, 0.00, 0.00, 0.00, 50.00, 'Unpaid', NULL);

-- Commit all 3 dependent operations together
COMMIT;
-- In case of any constraint error, MySQL would execute: ROLLBACK;
