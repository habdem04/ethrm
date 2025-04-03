frappe.ui.form.on("Disciplinary Action", {
    // Validation: If is_file_attached is checked, we verify that at least one file is attached.
    validate: function(frm) {
        console.log("is_file_attached:", frm.doc.is_file_attached);
        if (frm.doc.is_file_attached) {
            let attachments = (frm.get_docinfo() && frm.get_docinfo().attachments) || [];
            console.log("Attachments found:", attachments);
            if (attachments.length === 0) {
                frappe.msgprint(__("Please attach a file using the default attachment option on the left sidebar."));
                frappe.validated = false;
            }
        }
    },

    // Refresh event binds a click listener to the default attachment field.
    refresh: function(frm) {
        if (frm.fields_dict.attach_file) {
            // Remove any previous binding to avoid duplicates.
            frm.fields_dict.attach_file.$wrapper.off("click.preview_attachment");
            // Bind click event on anchor tags within the attach_file field.
            frm.fields_dict.attach_file.$wrapper.on("click.preview_attachment", "a", function(e) {
                e.preventDefault(); // Prevent the default download behavior.
                let file_url = $(this).attr("href");
                console.log("Attachment clicked. File URL:", file_url);
                if (!file_url) {
                    frappe.msgprint("File URL not found. Cannot preview attachment.");
                    return;
                }
                open_attachment_preview(file_url);
            });
        }
    }
});

/* 
  getPreviewHTML() determines what preview code to display based on the file extension.
  For Office files it returns a link that uses the local Office URI scheme,
  so clicking the link opens the file in your locally-installed Office.
*/
function getPreviewHTML(file_url) {
    // Ensure the URL is absolute.
    let absolute_file_url = file_url;
    if (!absolute_file_url.startsWith("http")) {
        absolute_file_url = window.location.origin + file_url;
    }

    // Determine file extension.
    let ext = absolute_file_url.split('.').pop().toLowerCase();

    // For PDF files, embed them.
    if (ext === 'pdf') {
        return `<embed src="${absolute_file_url}" type="application/pdf" width="100%" height="500px" />`;
    }
    // For MS Word files.
    else if (['doc', 'docx'].includes(ext)) {
        return `<a href="ms-word:ofv|u|${absolute_file_url}" target="_blank" style="font-size:16px;">Click here to preview in MS Word</a>`;
    }
    // For Excel files.
    else if (['xls', 'xlsx'].includes(ext)) {
        return `<a href="ms-excel:ofv|u|${absolute_file_url}" target="_blank" style="font-size:16px;">Click here to preview in MS Excel</a>`;
    }
    // For PowerPoint files.
    else if (['ppt', 'pptx'].includes(ext)) {
        return `<a href="ms-powerpoint:ofv|u|${absolute_file_url}" target="_blank" style="font-size:16px;">Click here to preview in MS PowerPoint</a>`;
    }
    // For video files.
    else if (['mp4', 'webm', 'ogg'].includes(ext)) {
        return `<video width="100%" height="500px" controls>
                    <source src="${absolute_file_url}" type="video/${ext}">
                    Your browser does not support the video tag.
                </video>`;
    }
    // For images.
    else if (['png', 'jpg', 'jpeg', 'gif'].includes(ext)) {
        return `<img src="${absolute_file_url}" style="width:100%; max-height:500px; object-fit:contain;" alt="Attachment" />`;
    }
    // Fallback for unsupported file types.
    else {
        return `<p>Preview not available for this file type.
                <a href="${absolute_file_url}" target="_blank">Download file</a></p>`;
    }
}

/* 
  open_attachment_preview() creates a dialog with a full-screen style and loads the preview HTML.
  For Office files, the preview is a clickable link that, when clicked, launches your local Office app.
*/
function open_attachment_preview(file_url) {
    // Convert relative URL to an absolute URL.
    let absolute_file_url = file_url;
    if (!absolute_file_url.startsWith("http")) {
        absolute_file_url = window.location.origin + encodeURI(file_url);
    } else {
        absolute_file_url = encodeURI(file_url);
    }
    console.log("Opening preview for URL:", absolute_file_url);

    // Obtain the appropriate preview HTML based on file type.
    let preview_html = getPreviewHTML(absolute_file_url);

    // Create the dialog.
    let d = new frappe.ui.Dialog({
        title: "Document Preview",
        fields: [
            {
                fieldtype: "HTML",
                fieldname: "preview_html"
            }
        ],
        primary_action_label: "Close",
        primary_action() {
            d.hide();
        }
    });
    d.show();
    d.fields_dict.preview_html.$wrapper.html(preview_html);

    // Apply full-screen styling after rendering the dialog.
    setTimeout(function(){
        d.$wrapper.find('.modal-dialog').css({
            "width": "100%",
            "max-width": "100vw",
            "margin": "0",
            "padding": "0",
            "height": "100vh"
        });
        d.$wrapper.find('.modal-content').css({
            "height": "100vh",
            "border": "none",
            "border-radius": "0"
        });
        d.$wrapper.find('.modal-body').css({
            "height": "calc(100vh - 65px)",  // Adjust this if you have a header/footer.
            "overflow-y": "auto"
        });
    }, 50);
}
