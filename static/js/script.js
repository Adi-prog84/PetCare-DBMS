/**
 * PetCare+ — Smart Pet Clinic Management System
 * Client-side Interactions, Modals, Dynamic Calculators
 * College DBMS Project
 */

document.addEventListener('DOMContentLoaded', () => {

    // ----------------------------------------------------------------
    // 1. Modal Trigger and Dismiss Handler
    // ----------------------------------------------------------------
    const modalOpenButtons = document.querySelectorAll('[data-modal-open]');
    const modalCloseButtons = document.querySelectorAll('.modal-close, [data-modal-close]');

    modalOpenButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = btn.getAttribute('data-modal-open');
            const targetModal = document.getElementById(targetId);
            if (targetModal) {
                targetModal.classList.add('open');
            }
        });
    });

    modalCloseButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const modal = btn.closest('.modal-backdrop');
            if (modal) {
                modal.classList.remove('open');
            }
        });
    });

    // Close modal when clicking outside the dialog content
    document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
        backdrop.addEventListener('click', (e) => {
            if (e.target === backdrop) {
                backdrop.classList.remove('open');
            }
        });
    });

    // ----------------------------------------------------------------
    // 2. Dynamic Fee Auto-Calculation in Billing Forms
    // ----------------------------------------------------------------
    function setupBillingCalculator(form) {
        if (!form) return;
        const consultInput = form.querySelector('input[name="consultation_fee"]');
        const treatInput = form.querySelector('input[name="treatment_fee"]');
        const medInput = form.querySelector('input[name="medicine_fee"]');
        const vaxInput = form.querySelector('input[name="vaccination_fee"]');
        const totalDisplay = form.querySelector('.total-amount-calc');

        function calculate() {
            const c = parseFloat(consultInput ? consultInput.value : 0) || 0;
            const t = parseFloat(treatInput ? treatInput.value : 0) || 0;
            const m = parseFloat(medInput ? medInput.value : 0) || 0;
            const v = parseFloat(vaxInput ? vaxInput.value : 0) || 0;
            const total = c + t + m + v;
            if (totalDisplay) {
                totalDisplay.textContent = '₹/USD ' + total.toFixed(2);
            }
        }

        [consultInput, treatInput, medInput, vaxInput].forEach(inp => {
            if (inp) inp.addEventListener('input', calculate);
        });
        calculate();
    }

    document.querySelectorAll('.billing-calc-form').forEach(setupBillingCalculator);

    // ----------------------------------------------------------------
    // 3. Quick Demo Login Credentials Auto-Fill
    // ----------------------------------------------------------------
    const demoChips = document.querySelectorAll('.demo-chip');
    demoChips.forEach(chip => {
        chip.addEventListener('click', () => {
            const u = chip.getAttribute('data-user');
            const p = chip.getAttribute('data-pass');
            const uInput = document.getElementById('username');
            const pInput = document.getElementById('password');
            if (uInput && pInput) {
                uInput.value = u;
                pInput.value = p;
                uInput.focus();
            }
        });
    });

    // ----------------------------------------------------------------
    // 4. Alert Auto-Dismiss
    // ----------------------------------------------------------------
    document.querySelectorAll('.alert-close').forEach(btn => {
        btn.addEventListener('click', () => {
            const alert = btn.closest('.alert');
            if (alert) {
                alert.style.transition = 'opacity 0.3s ease';
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 300);
            }
        });
    });

});

// Global confirmation function for deletion forms
function confirmDelete(message) {
    return confirm(message || 'Are you sure you want to delete this record? This action cannot be undone.');
}
