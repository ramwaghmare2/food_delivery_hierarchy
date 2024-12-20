/*!
    * Start Bootstrap - SB Admin v7.0.7 (https://startbootstrap.com/template/sb-admin)
    * Copyright 2013-2023 Start Bootstrap
    * Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-sb-admin/blob/master/LICENSE)
    */
    // 
// Scripts
// 

window.addEventListener('DOMContentLoaded', event => {

    // Toggle the side navigation
    const sidebarToggle = document.body.querySelector('#sidebarToggle');
    if (sidebarToggle) {
        // Uncomment Below to persist sidebar toggle between refreshes
        // if (localStorage.getItem('sb|sidebar-toggle') === 'true') {
        //     document.body.classList.toggle('sb-sidenav-toggled');
        // }
        sidebarToggle.addEventListener('click', event => {
            event.preventDefault();
            document.body.classList.toggle('sb-sidenav-toggled');
            localStorage.setItem('sb|sidebar-toggle', document.body.classList.contains('sb-sidenav-toggled'));
        });
    }

});


// Pagination Script
document.addEventListener('DOMContentLoaded', function () {
    const rowsPerPage = 10;
    const rows = document.querySelectorAll('#OrderTable tbody tr');
    const totalRows = rows.length;
    const totalPages = Math.ceil(totalRows / rowsPerPage);
    const paginationControls = document.getElementById('pagination-controls');

    let currentPage = 1;

    function paginate() {
        // Hide all rows
        rows.forEach(row => row.style.display = 'none');

        // Show rows for the current page
        const startIdx = (currentPage - 1) * rowsPerPage;
        const endIdx = startIdx + rowsPerPage;
        for (let i = startIdx; i < endIdx && i < rows.length; i++) {
            rows[i].style.display = '';
        }

        // Update pagination controls
        paginationControls.innerHTML = ''; // Clear existing controls

        // Create Previous Arrow
        const prevButton = document.createElement('button');
        prevButton.textContent = '<';
        prevButton.classList.add('arrow');
        if (currentPage === 1) prevButton.classList.add('disabled');
        prevButton.onclick = function () {
            if (currentPage > 1) {
                currentPage--;
                paginate();
            }
        };
        paginationControls.appendChild(prevButton);

        // Display Current Page Number
        const pageDisplay = document.createElement('span');
        pageDisplay.textContent = `${currentPage}`;
        pageDisplay.classList.add('page-display');
        paginationControls.appendChild(pageDisplay);

        // Create Next Arrow
        const nextButton = document.createElement('button');
        nextButton.textContent = '>';
        nextButton.classList.add('arrow');
        if (currentPage === totalPages) nextButton.classList.add('disabled');
        nextButton.onclick = function () {
            if (currentPage < totalPages) {
                currentPage++;
                paginate();
            }
        };
        paginationControls.appendChild(nextButton);
    }

    // Initial pagination
    paginate();
});

function togglePassword() {
    var passwordField = document.getElementById("password");
    var eyeIcon = document.getElementById("eye-icon");
    
    // Toggle the type attribute between password and text
    if (passwordField.type === "password") {
        passwordField.type = "text";
        eyeIcon.classList.remove("fa-eye");
        eyeIcon.classList.add("fa-eye-slash");
    } else {
        passwordField.type = "password";
        eyeIcon.classList.remove("fa-eye-slash");
        eyeIcon.classList.add("fa-eye");
    }
}

function toggleRePassword() {
    var rePasswordField = document.getElementById("re_password");
    var reEyeIcon = document.getElementById("re-eye-icon");
    
    // Toggle the type attribute between password and text
    if (rePasswordField.type === "password") {
        rePasswordField.type = "text";
        reEyeIcon.classList.remove("fa-eye");
        reEyeIcon.classList.add("fa-eye-slash");
    } else {
        rePasswordField.type = "password";
        reEyeIcon.classList.remove("fa-eye-slash");
        reEyeIcon.classList.add("fa-eye");
    }
}