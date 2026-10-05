// Hospital Management System - Simple Client Script

document.addEventListener('DOMContentLoaded', function () {
  // 1. Auto-calculate total in Generate Bill page
  const consultInput = document.getElementById('consultation_fee');
  const medicineInput = document.getElementById('medicine_charges');
  const testInput = document.getElementById('test_charges');
  const otherInput = document.getElementById('other_charges');
  const discountInput = document.getElementById('discount');
  const totalDisplay = document.getElementById('total_display');
  const doctorSelect = document.getElementById('doctor_id');

  function calculateBillTotal() {
    if (!totalDisplay) return;

    const consult = parseFloat(consultInput?.value) || 0;
    const medicine = parseFloat(medicineInput?.value) || 0;
    const test = parseFloat(testInput?.value) || 0;
    const other = parseFloat(otherInput?.value) || 0;
    const discount = parseFloat(discountInput?.value) || 0;

    const subtotal = consult + medicine + test + other;
    const total = Math.max(0, subtotal - discount);

    totalDisplay.innerText = '₹' + total.toFixed(2);
  }

  // Auto-fill consultation fee when doctor is selected
  if (doctorSelect) {
    doctorSelect.addEventListener('change', function () {
      const selectedOption = doctorSelect.options[doctorSelect.selectedIndex];
      const fee = selectedOption.getAttribute('data-fee');
      if (fee && consultInput) {
        consultInput.value = fee;
        calculateBillTotal();
      }
    });
  }

  // Attach calculation events to input fields
  const billingInputs = [consultInput, medicineInput, testInput, otherInput, discountInput];
  billingInputs.forEach(input => {
    if (input) {
      input.addEventListener('input', calculateBillTotal);
      input.addEventListener('change', calculateBillTotal);
    }
  });

  // Run initial calculation if on bill page
  calculateBillTotal();

  // 2. Set default date for appointment booking to today if empty
  const aptDateInput = document.getElementById('appointment_date');
  if (aptDateInput && !aptDateInput.value) {
    const today = new Date().toISOString().split('T')[0];
    aptDateInput.value = today;
    aptDateInput.setAttribute('min', today);
  }
});

// 3. Print helper function for bill
function printBill() {
  window.print();
}
