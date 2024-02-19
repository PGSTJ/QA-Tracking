document.addEventListener("DOMContentLoaded", function () {
    addQaPopup();
    checkTrackerLoop();
});

function addQaPopup() {
    // Get elements
    const addQALink = document.getElementById("add-qa-link");
    const popupForm = document.getElementById("add-prospective-popup");
    const overLay = document.getElementById("qaf-overlay");

    // Show popup on link click
    addQALink.addEventListener("click", function (event) {
        event.preventDefault();
        popupForm.style.display = "block";
        overLay.style.visibility = "visible";
    });

    // Hide popup on form submission
    const qaForm = document.getElementById("qa-form");
    qaForm.addEventListener("submit", function (event) {
        event.preventDefault();
        overLay.style.visibility = "hidden";
        // Handle form submission using AJAX or other method
        // After submission, you can reload the page or update the content dynamically
        // For simplicity, let's reload the page
        window.location.href = '/home';
    });
}

function checkTrackerLoop() {
    var prospectiveRows = document.querySelectorAll('#prospective .table-view table tr');
    var dueRows = document.querySelectorAll('#due .table-view table tr')
    var hiddenNoneDivPro = document.querySelector('#prospective .hidden-none');
    var hiddenNoneDivDue = document.querySelector('#due .hidden-none');

    console.log("Prospective rows length:", prospectiveRows.length);
    console.log("Due rows length:", dueRows.length);

    if (prospectiveRows.length === 1) {
        hiddenNoneDivPro.style.display = 'block';
    } else {
        hiddenNoneDivPro.style.display = 'none';
    }

    if (dueRows.length === 1) {
        hiddenNoneDivDue.style.display = 'block';
    } else {
        hiddenNoneDivDue.style.display = 'none';
    }

}
