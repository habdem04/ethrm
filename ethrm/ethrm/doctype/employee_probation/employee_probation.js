// Copyright (c) 2025, ELIF TECHNOLOGIES PLC and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Employee Probation", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on('Employee Probation', {
    // When Date of Joining changes
    date_of_joining: function(frm) {
        calculateProbationEndDate(frm);
    },
    // When In Probation Days changes
    in_probation_days: function(frm) {
        calculateProbationEndDate(frm);
    },

    // date_of_joining_ec: function(frm) {
    //     const ethiopian_date = frm.doc.date_of_joining_ec;

    //     // // Ensure Ethiopian date is exactly 10 characters
    //     // if (!ethiopian_date) {
    //     //     frappe.msgprint(__('Invalid Ethiopian date format. It must be in "DD/MM/YYYY" format.'));
    //     //     return;
    //     // }

    //     frappe.call({
    //         method: 'ethrm.utils.date_convertor.ethiopian_to_gregorian',
    //         args: { ethiopian_date: ethiopian_date },
    //         callback: function(r) {
    //             if (r.message) {
    //                 frm.set_value('date_of_joining', r.message);
    //             }
    //         }
    //     });
    // },

    // date_of_joining: function(frm) {
    //     const gregorian_date = frm.doc.date_of_joining;

    //     // // Ensure Gregorian date is exactly 10 characters
    //     // if (!gregorian_date) {
    //     //     frappe.msgprint(__('Invalid Gregorian date format. It must be in "YYYY-MM-DD" format.'));
    //     //     return;
    //     // }

    //     frappe.call({
    //         method: 'ethrm.utils.date_convertor.gregorian_to_ethiopian',
    //         args: { gregorian_date: gregorian_date },
    //         callback: function(r) {
    //             if (r.message) {
    //                 frm.set_value('date_of_joining_ec', r.message);
    //             }
    //         }
    //     });
    // }

});

// Helper function to call the server-side method and set the End Date (Gregorian)
function calculateProbationEndDate(frm) {
    if (frm.doc.date_of_joining && frm.doc.in_probation_days) {
        frappe.call({
            method: 'ethrm.utils.probation_end_date.calculate_probation_end_date',
            args: {
                start_date: frm.doc.date_of_joining,
                in_probation_days: frm.doc.in_probation_days
            },
            callback: function(r) {
                if (r.message) {
                    frm.set_value('end_date_gc', r.message);
                }
            }
        });
    }
}
