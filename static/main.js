document.addEventListener("DOMContentLoaded", function () {
    checkTrackerLoop();
    addQaPopup();
    addNsPopup();
});

function addQaPopup() {
    // Get elements
    const addQALink = document.getElementById("add-qa-link");
    const popupForm = document.getElementById("add-prospective-popup");
    const overLay = document.getElementById("popup-overlay");

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
        popupForm.style.display = "none";
        overLay.style.visibility = "hidden";

        var formData = new FormData(this);
        console.log(formData)

        var xhr = new XMLHttpRequest();
        xhr.open("POST", "/submit_prospective", true);
        xhr.onreadystatechange = function() {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                if (xhr.status === 200) {
                    // Handle successful response
                    console.log("Form submitted successfully");
                    // Optionally, redirect to another page after successful submission
                    // window.location.href = "/home";
                } else {
                    // Handle error response
                    console.error("Form submission failed");
                }
            }   
        } 
        xhr.send(formData)
        
        // Handle form submission using AJAX or other method
        // After submission, you can reload the page or update the content dynamically
        // For simplicity, let's reload the page
        // window.location.href = '/';
    });
}

function addNsPopup() {
    // Get elements
    const addScribeLink = document.getElementById("add-scribe-link")
    const popupNsForm = document.getElementById("add-scribe-popup");

    const overLay = document.getElementById("popup-overlay");
    
    addScribeLink.addEventListener("click", function (event) {
        event.preventDefault();
        popupNsForm.style.display = "block";
        overLay.style.visibility = "visible";
    });
    
    // Hide popup on form submission
    const qaForm = document.getElementById("new-scribe-form");
    qaForm.addEventListener("submit", function (event) {
        event.preventDefault();
        overLay.style.visibility = "hidden";
        popupNsForm.style.display = "none";

        var formData = new FormData(this);

        console.log(formData)

        var xhr = new XMLHttpRequest();
        xhr.open("POST", "/add_new_scribe", true);
        xhr.onreadystatechange = function() {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                if (xhr.status === 200) {
                    // Handle successful response
                    console.log("Form submitted successfully");
                    // Optionally, redirect to another page after successful submission
                    window.location.href = "/home";
                } else {
                    // Handle error response
                    console.error("Form submission failed");
                }
            }   
        } 
        xhr.send(formData)

        // Handle form submission using AJAX or other method
        // After submission, you can reload the page or update the content dynamically
        // For simplicity, let's reload the page
        // window.location.href = '/home';
    });
}

function checkTrackerLoop() {
    console.log('checkTrackerLoop function called');
    var prospectiveRows = document.querySelectorAll('#prospective .table-view table tr');
    var dueRows = document.querySelectorAll('#due .table-view table tr')
    var hiddenNoneDivPro = document.querySelector('#prospective .hidden-none');
    var hiddenNoneDivDue = document.querySelector('#due .hidden-none');

    console.log("Prospective rows length:", prospectiveRows.length);
    console.log("Due rows length:", dueRows.length);

    if (prospectiveRows.length > 1) {
        hiddenNoneDivPro.style.display = 'none';
    } else {
        hiddenNoneDivPro.style.display = 'block';
    }

    if (dueRows.length > 1) {
        hiddenNoneDivDue.style.display = 'none';
    } else {
        hiddenNoneDivDue.style.display = 'block';
    }

}
