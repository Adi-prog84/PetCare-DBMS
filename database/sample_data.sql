-- ====================================================================
-- PetCare+ — Smart Pet Clinic Management System
-- Sample Data Script
-- Fictional, realistic data for college DBMS demonstration
-- ====================================================================

USE petcare_db;

-- 1. Users (Passwords hashed using Werkzeug scrypt)
-- admin / admin123
-- receptionist / recep123
-- drsmith / vet123
-- dremily / vet123
INSERT INTO users (username, password, role, full_name) VALUES
('admin', 'scrypt:32768:8:1$DWibgd9W92Xv4KOQ$e6f4f6378ccd6e18378d4e140073a1d3aff68278bea491fbae674d23f84f8dc252227d00a05cfe203495dbdc7b807fd25dbffc5f5361bf47fa16708edd5c9073', 'Admin', 'Admin Officer'),
('receptionist', 'scrypt:32768:8:1$utIWz8CTL8XXGjOx$f9f4456a8ab78f9eca3e2b78d172f15c5e0f66ade2964cc05c4822f023ae8d381b9efe5e0436e00fce6ff2d584a65c3307978bdd4cba9926a186c7026f13eb6b', 'Receptionist', 'Sarah Jenkins'),
('drsmith', 'scrypt:32768:8:1$QyilzQrr7S7Fx1H9$3fccd2241d95ffe97a946ee93ce6d9d6ca27918abf7e55481d5e953cb8dfa1fcb991150b48095b9d0e7c3d1105140ddb5f57024c8751b4c2e6233a204282bf85', 'Veterinarian', 'Dr. Robert Smith'),
('dremily', 'scrypt:32768:8:1$QyilzQrr7S7Fx1H9$3fccd2241d95ffe97a946ee93ce6d9d6ca27918abf7e55481d5e953cb8dfa1fcb991150b48095b9d0e7c3d1105140ddb5f57024c8751b4c2e6233a204282bf85', 'Veterinarian', 'Dr. Emily Chen');

-- 2. Pet Owners (7 Owners)
INSERT INTO pet_owners (owner_id, name, phone, email, address) VALUES
(1, 'Michael Brown', '9876543210', 'michael.brown@example.com', '124 Elm Street, Springfield'),
(2, 'Jessica Davis', '9876543211', 'jessica.davis@example.com', '45 Maple Avenue, Springfield'),
(3, 'David Wilson', '9876543212', 'david.wilson@example.com', '88 Oak Lane, Greenfield'),
(4, 'Amanda Taylor', '9876543213', 'amanda.taylor@example.com', '210 Pine Road, Springfield'),
(5, 'Christopher Martinez', '9876543214', 'c.martinez@example.com', '77 Birch Boulevard, Lakeside'),
(6, 'Priya Sharma', '9876543215', 'priya.sharma@example.com', '32 Blossom Hill, Springfield'),
(7, 'Daniel Anderson', '9876543216', 'daniel.a@example.com', '15 Cedar Court, Greenfield');

-- 3. Veterinarians (4 Doctors)
INSERT INTO veterinarians (vet_id, name, specialization, phone, email) VALUES
(1, 'Dr. Robert Smith', 'Canine Internal Medicine', '9123456780', 'dr.smith@petcareplus.com'),
(2, 'Dr. Emily Chen', 'Feline Medicine & Soft Tissue Surgery', '9123456781', 'dr.chen@petcareplus.com'),
(3, 'Dr. Marcus Vance', 'Avian & Exotic Animal Medicine', '9123456782', 'dr.vance@petcareplus.com'),
(4, 'Dr. Sophia Patel', 'Veterinary Orthopedics & Rehabilitation', '9123456783', 'dr.patel@petcareplus.com');

-- 4. Pets (11 Pets belonging to the owners)
INSERT INTO pets (pet_id, owner_id, pet_name, species, breed, gender, date_of_birth, weight) VALUES
(1, 1, 'Max', 'Dog', 'Golden Retriever', 'Male', '2021-04-15', 31.50),
(2, 1, 'Bella', 'Cat', 'Persian', 'Female', '2022-08-10', 4.20),
(3, 2, 'Rocky', 'Dog', 'German Shepherd', 'Male', '2020-01-22', 36.80),
(4, 2, 'Luna', 'Cat', 'Siamese', 'Female', '2023-03-05', 3.80),
(5, 3, 'Charlie', 'Dog', 'Beagle', 'Male', '2022-11-19', 12.40),
(6, 4, 'Milo', 'Cat', 'Maine Coon', 'Male', '2021-06-30', 7.90),
(7, 4, 'Kiwi', 'Bird', 'Cockatiel', 'Female', '2023-09-12', 0.11),
(8, 5, 'Daisy', 'Dog', 'Labrador Retriever', 'Female', '2019-12-01', 28.60),
(9, 6, 'Coco', 'Rabbit', 'Holland Lop', 'Male', '2023-05-18', 1.85),
(10, 6, 'Bruno', 'Dog', 'Rottweiler', 'Male', '2021-02-14', 42.00),
(11, 7, 'Oliver', 'Cat', 'British Shorthair', 'Male', '2022-10-04', 5.10);

-- 5. Appointments (14 Appointments across different dates & statuses)
INSERT INTO appointments (appointment_id, pet_id, vet_id, appointment_date, appointment_time, reason, status) VALUES
(1, 1, 1, '2026-09-10', '09:30:00', 'Annual checkup and lethargy check', 'Completed'),
(2, 2, 2, '2026-09-11', '10:15:00', 'Persistent sneezing and eye discharge', 'Completed'),
(3, 3, 4, '2026-09-12', '11:00:00', 'Limping on hind left leg after fetch', 'Completed'),
(4, 5, 1, '2026-09-15', '14:00:00', 'Ear scratching and head shaking', 'Completed'),
(5, 6, 2, '2026-09-18', '15:30:00', 'Digestive issues and vomiting', 'Completed'),
(6, 7, 3, '2026-09-20', '11:30:00', 'Feather plucking and diet consultation', 'Completed'),
(7, 8, 1, '2026-09-22', '16:00:00', 'Skin allergy and redness on belly', 'Completed'),
(8, 1, 1, '2026-09-25', '10:00:00', 'Follow-up blood test check', 'Completed'),
(9, 4, 2, '2026-09-28', '10:00:00', 'Routine kitten health exam', 'Scheduled'),
(10, 10, 4, '2026-09-28', '11:30:00', 'Hip dysplasia screening', 'Scheduled'),
(11, 9, 3, '2026-09-29', '14:30:00', 'Dental overgrown incisors check', 'Scheduled'),
(12, 11, 2, '2026-09-30', '16:00:00', 'Hairball treatment and grooming advice', 'Scheduled'),
(13, 3, 1, '2026-09-21', '09:00:00', 'Kennel cough follow-up', 'Cancelled'),
(14, 5, 1, '2026-10-02', '10:30:00', 'Pre-travel rabies and health certificate', 'Scheduled');

-- 6. Treatments (For Completed Appointments)
INSERT INTO treatments (treatment_id, appointment_id, diagnosis, treatment_description, treatment_date, notes) VALUES
(1, 1, 'Mild Dehydration and Fatigue', 'Subcutaneous fluid administration and vitamin B12 supplement injection.', '2026-09-10', 'Advised 48 hours of rest and increased water intake with electrolytes.'),
(2, 2, 'Upper Respiratory Infection (Feline Herpesvirus)', 'Ophthalmic antibacterial ointment and oral antiviral syrup.', '2026-09-11', 'Isolate from other household cats for 7 days. Clean eyes twice daily.'),
(3, 3, 'Mild Patellar Luxation (Grade 1)', 'Physical manipulation, anti-inflammatory injection, and light leg wrap.', '2026-09-12', 'Strict crate rest for 5 days. Avoid stairs and vigorous running.'),
(4, 4, 'Bacterial & Yeast Otitis Externa', 'Deep ear canal cleaning and flushing under mild topical sedation.', '2026-09-15', 'Apply otic suspension daily. Keep ears dry during baths.'),
(5, 5, 'Acute Dietary Gastritis', 'Anti-emetic injection (Cerenia) and gastrointestinal protectant paste.', '2026-09-18', 'Transition to bland boiled chicken and rice diet for 3 days.'),
(6, 6, 'Stress-induced Feather Plucking', 'Topical soothing spray and nutritional pellet diet formulation adjustment.', '2026-09-20', 'Provide foraging toys and rotate cage location away from direct draft.'),
(7, 7, 'Atopic Dermatitis (Flea Bite Allergy)', 'Medicated soothing bath, flea adulticide spot-on, and oral antihistamines.', '2026-09-22', 'Wash all bedding at home in hot water. Apply monthly flea prevention.'),
(8, 8, 'Normal Recovery - Blood Work Clear', 'Platelet and liver enzyme checkup. Everything within normal reference ranges.', '2026-09-25', 'Patient discharged with full bill of health.');

-- 7. Vaccinations (Preventative health tracking)
INSERT INTO vaccinations (vaccination_id, pet_id, vaccine_name, vaccination_date, next_due_date, notes) VALUES
(1, 1, 'Rabies (3-Year)', '2024-04-15', '2027-04-15', 'Standard 3-year canine rabies booster given subcutaneous left shoulder.'),
(2, 1, 'DHPP Core Dog Booster', '2025-09-10', '2026-10-10', 'Upcoming booster due in a couple of weeks.'),
(3, 2, 'FVRCP (Feline Viral Rhinotracheitis)', '2025-09-15', '2026-10-05', 'Annual feline core vaccine due soon.'),
(4, 2, 'Rabies (1-Year)', '2025-09-15', '2026-09-15', 'Annual feline rabies vaccine overdue by a few days.'),
(5, 3, 'Bordetella (Kennel Cough)', '2026-03-12', '2026-09-12', 'Overdue for boarding facility requirement.'),
(6, 3, 'DHPP Core Dog Booster', '2026-01-20', '2027-01-20', 'Healthy immunity confirmed.'),
(7, 5, 'Rabies (1-Year)', '2025-10-15', '2026-10-15', 'Due next month, reminder sent to owner.'),
(8, 6, 'FVRCP (Feline Core)', '2026-02-10', '2027-02-10', 'Annual booster given without adverse reaction.'),
(9, 8, 'DHPP Core Dog Booster', '2025-12-05', '2026-12-05', 'Due in December.'),
(10, 8, 'Lyme Disease Vaccine', '2026-04-02', '2027-04-02', 'Recommended due to frequent hiking in woodland areas.'),
(11, 10, 'Rabies (1-Year)', '2025-10-01', '2026-10-01', 'Upcoming renewal due within a few days.');

-- 8. Prescriptions (Medications for treatments)
INSERT INTO prescriptions (prescription_id, treatment_id, medicine_name, dosage, frequency, duration, instructions) VALUES
(1, 1, 'Pet Nutri-Plus Gel', '5 ml', 'Twice daily', '7 days', 'Administer directly by mouth before meals.'),
(2, 2, 'Famciclovir Antiviral Syrup', '2.5 ml', 'Twice daily', '10 days', 'Keep refrigerated. Complete full course.'),
(3, 2, 'Terramycin Eye Ointment', 'Small strip', 'Three times daily', '7 days', 'Apply gently into conjunctival sac of both eyes.'),
(4, 3, 'Carprofen 75mg Tablets', '1 tablet', 'Once daily', '5 days', 'Must be administered with food to prevent gastric upset.'),
(5, 4, 'Otomax Ear Drops', '4 drops', 'Twice daily', '10 days', 'Massage base of ear gently after instilling drops.'),
(6, 4, 'Cephalexin 250mg', '1 capsule', 'Twice daily', '7 days', 'Give with meals for bacterial skin infection.'),
(7, 5, 'Sucralfate Oral Suspension', '3 ml', 'Three times daily', '4 days', 'Give on an empty stomach 1 hour prior to feeding.'),
(8, 7, 'Apoquel 5.4mg', '1 tablet', 'Twice daily for 7 days then once daily', '14 days', 'For itching relief. Report any drowsiness.'),
(9, 7, 'Bravecto Chewable', '1 chew', 'Single dose', '90 days', 'Chewable flea and tick preventive with meal.');

-- 9. Bills (Invoices for appointments)
INSERT INTO bills (bill_id, appointment_id, consultation_fee, treatment_fee, medicine_fee, vaccination_fee, total_amount, payment_status, payment_date) VALUES
(1, 1, 50.00, 45.00, 25.00, 0.00, 120.00, 'Paid', '2026-09-10'),
(2, 2, 50.00, 30.00, 48.00, 0.00, 128.00, 'Paid', '2026-09-11'),
(3, 3, 60.00, 75.00, 35.00, 0.00, 170.00, 'Paid', '2026-09-12'),
(4, 4, 50.00, 55.00, 42.00, 0.00, 147.00, 'Unpaid', NULL),
(5, 5, 50.00, 60.00, 30.00, 0.00, 140.00, 'Paid', '2026-09-18'),
(6, 6, 65.00, 40.00, 20.00, 0.00, 125.00, 'Paid', '2026-09-20'),
(7, 7, 50.00, 60.00, 78.00, 0.00, 188.00, 'Unpaid', NULL),
(8, 8, 40.00, 30.00, 0.00, 0.00, 70.00, 'Paid', '2026-09-25');
