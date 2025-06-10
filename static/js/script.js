// Handle image upload
document.getElementById('upload-form').addEventListener('submit', function (e) {
    e.preventDefault();

    const resultDiv = document.getElementById('result');
    resultDiv.innerHTML = getLoadingSpinner("Processing image...");

    const formData = new FormData();
    const image = document.getElementById('image').files[0];
    formData.append('image', image);

    fetch('/upload-image', {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        displayResult(data);
    })
    .catch(err => {
        showError("An error occurred while uploading the image.");
    });
});

// Handle direct number input
document.getElementById('number-form').addEventListener('submit', function (e) {
    e.preventDefault();

    const number = document.getElementById('number').value.trim();
    const resultDiv = document.getElementById('result');

    if (!number) {
        showError("Please enter a vehicle number.");
        return;
    }

    resultDiv.innerHTML = getLoadingSpinner("Checking number...");

    fetch('/check-number', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ number_plate: number })
    })
    .then(res => res.json())
    .then(data => {
        displayResult(data);
    })
    .catch(err => {
        showError("An error occurred while checking the number.");
    });
});

// Utility: Show spinner
function getLoadingSpinner(message) {
    return `
        <div class="alert alert-info d-flex align-items-center" role="alert">
            <i class="fas fa-spinner fa-spin me-2"></i> ${message}
        </div>
    `;
}

// Utility: Show error message
function showError(message) {
    document.getElementById('result').innerHTML = `
        <div class="alert alert-danger" role="alert">
            <i class="fas fa-circle-exclamation me-2"></i> ${message}
        </div>
    `;
}

// Utility: Display structured result
function displayResult(data) {
    const resultDiv = document.getElementById('result');

    if (!data || Object.keys(data).length === 0 || data.error) {
        resultDiv.innerHTML = `
            <div class="alert alert-warning" role="alert">
                <i class="fas fa-triangle-exclamation me-2"></i>
                ${data.error || "No matching record found."}
            </div>
        `;
        return;
    }

    resultDiv.innerHTML = `
        <div class="card shadow-sm">
            <div class="card-body">
                <h5 class="card-title text-primary">
                    <i class="fas fa-id-card me-2"></i> Vehicle Details
                </h5>
                <ul class="list-group list-group-flush mt-3">
                    <li class="list-group-item"><strong>Owner:</strong> ${data.owner || "N/A"}</li>
                    <li class="list-group-item"><strong>Vehicle Number:</strong> ${data.number_plate || "N/A"}</li>
                    <li class="list-group-item"><strong>Contact:</strong> ${data.phone_number || "N/A"}</li>
                    <li class="list-group-item"><strong>Address:</strong> ${data.address || "N/A"}</li>
                </ul>
            </div>
        </div>
    `;
}
