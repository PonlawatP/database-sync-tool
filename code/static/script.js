const startButton = document.getElementById('start-sync');
const stopButton = document.getElementById('stop-sync');
const syncStatusElement = document.getElementById('sync-status');
const lastSyncElement = document.getElementById('last-sync');
const currentOperationElement = document.getElementById('current-operation');
const progressBar = document.getElementById('progress-bar');
const progressText = document.getElementById('progress-text');

let statusCheckInterval;

async function updateStatus() {
    try {
        const response = await fetch('/sync/status');
        const data = await response.json();
        
        syncStatusElement.textContent = data.is_running ? 'Running' : data.last_status != null ? data.last_status.charAt(0).toUpperCase() + data.last_status.slice(1) : 'Not Running';
        lastSyncElement.textContent = data.last_sync || 'Never';
        currentOperationElement.textContent = data.current_operation || 'None';
        
        startButton.disabled = data.is_running;
        stopButton.disabled = !data.is_running;
        
        if (data.is_running === false) {
            syncStatusElement.style.color = 'red';
        } else if (data.is_running === true || data.last_status === 'success') {
            syncStatusElement.style.color = 'green';
        }

        progressBar.style.width = `${data.progress.toFixed(0)}%`;
        progressText.textContent = `${data.progress.toFixed(0)}%`;
    } catch (error) {
        console.error('Error fetching status:', error);
    }
}

startButton.addEventListener('click', async () => {
    try {
        fetch('/sync', {
            method: 'POST'
        });
        
        updateStatus();
    } catch (error) {}
});

stopButton.addEventListener('click', async () => {
    try {
        const response = await fetch('/sync/stop', {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('Failed to stop sync');
        }
        
        updateStatus();
    } catch (error) {
        console.error('Error stopping sync:', error);
        alert('Failed to stop sync process');
    }
});

// Update status every 2 seconds
statusCheckInterval = setInterval(updateStatus, 500);

// Initial status check
updateStatus(); 