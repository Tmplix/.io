document.getElementById('downloadForm').addEventListener('submit', function (event) {
    event.preventDefault(); // Prevent the default form submission

    const url = document.getElementById('url').value;
    const quality = document.getElementById('quality').value;
    const convertTo = document.getElementById('convert_to').value;

    // Show status message
    document.getElementById('statusMessage').classList.remove('hidden');
    document.getElementById('status').textContent = 'Starting download...';

    // Send the data to the backend using fetch
    fetch('/download', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            url: url,
            quality: quality,
            convert_to: convertTo,
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.download_id) {
            checkDownloadStatus(data.download_id);
        }
    })
    .catch(error => {
        document.getElementById('status').textContent = 'Error: ' + error.message;
    });
});

// Function to check the download status
function checkDownloadStatus(downloadId) {
    setInterval(function () {
        fetch(`/status/${downloadId}`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('status').textContent = data.status;

                if (data.status === 'Completed') {
                    clearInterval(this);
                    alert('Download completed!');
                }
            });
    }, 3000); // Check every 3 seconds
}
