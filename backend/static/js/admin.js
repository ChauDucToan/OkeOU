function servedAll() {
    fetch('/api/admin/serve_all', {
        method: 'GET'
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 200) {
                alert('All orders have been marked as served.');
                location.reload();
            } else {
                alert('Failed to mark all orders as served.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while processing your request.');
        });
}