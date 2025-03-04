frappe.ui.form.on('Ethiopian Date Convertor', {
    from_ec_date: function(frm) {
        const ethiopian_date = frm.doc.from_ec_date;

        // Ensure Ethiopian date is exactly 10 characters
        if (!ethiopian_date) {
            frappe.msgprint(__('Invalid Ethiopian date format. It must be in "DD/MM/YYYY" format.'));
            return;
        }

        frappe.call({
            method: 'ethrm.utils.date_convertor.ethiopian_to_gregorian',
            args: { ethiopian_date: ethiopian_date },
            callback: function(r) {
                if (r.message) {
                    frm.set_value('to_gc_date', r.message);
                }
            }
        });
    },

    from_gc_date: function(frm) {
        const gregorian_date = frm.doc.from_gc_date;

        // Ensure Gregorian date is exactly 10 characters
        if (!gregorian_date) {
            frappe.msgprint(__('Invalid Gregorian date format. It must be in "YYYY-MM-DD" format.'));
            return;
        }

        frappe.call({
            method: 'ethrm.utils.date_convertor.gregorian_to_ethiopian',
            args: { gregorian_date: gregorian_date },
            callback: function(r) {
                if (r.message) {
                    frm.set_value('to_ec_date', r.message);
                }
            }
        });
    }
});
