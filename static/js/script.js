// Handle image upload
document.getElementById('upload-form').addEventListener('submit', function (e) {
    e.preventDefault();

    const formData = new FormData();
    const image = document.getElementById('image').files[0];
    formData.append('image', image);

    fetch('/upload-image', {
        method: 'POST',
        body: formData
    }).then(res => res.json())
      .then(data => {
          document.getElementById('result').innerText = JSON.stringify(data, null, 2);
      })
      .catch(err => {
        document.getElementById('result').innerText = `Error: ${err}`;
    });
});

// Handle direct number input
document.getElementById('number-form').addEventListener('submit', function (e) {
    e.preventDefault();

    const number = document.getElementById('number').value;

    fetch('/check-number', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ number_plate: number })
    }).then(res => res.json())
      .then(data => {
          document.getElementById('result').innerText = JSON.stringify(data, null, 2);
      });
      
});
