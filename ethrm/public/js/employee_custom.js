// file: employee_custom.js
frappe.ui.form.on('Employee', {
    date_of_joining: function(frm) {
        if (frm.doc.date_of_joining) {
            frappe.call({
                method: 'ethrm.utils.probation_end_date.calculate_probation_end_date',
                args: {
                    start_date: frm.doc.date_of_joining
                },
                callback: function(r) {
                    if (!r.exc) {
                        frm.set_value('custom_probation_end_date', r.message);
                    }
                }
            });
        }
    }
});
