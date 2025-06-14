// Shared Header JavaScript Functions for AI Crypto Bot Dashboards

// Function to format UTC time consistently (24-hour format)
function formatUTCTime(date) {
    if (!date) return 'Unknown';
    
    // Ensure we have a Date object
    if (typeof date === 'string') {
        date = new Date(date + (date.includes('Z') ? '' : 'Z'));
    }
    
    // Format as 24-hour UTC time
    const options = {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        timeZone: 'UTC',
        hour12: false
    };
    
    return date.toLocaleString('en-GB', options) + ' UTC';
}

// Function to update the live clock
function updateClock() {
    const clockElement = document.getElementById('live-clock');
    if (clockElement) {
        const now = new Date();
        clockElement.innerHTML = 
            '<i class="far fa-clock me-1"></i>' + 
            formatUTCTime(now);
    }
}

// Function to format uptime
function formatUptime(seconds) {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    return `${days}d ${hours}h ${minutes}m`;
}

// Function to update bot status in header
async function updateBotStatus() {
    const uptimeElement = document.getElementById('bot-uptime');
    if (!uptimeElement) return;
    
    try {
        const response = await fetch('./data/cache/bot_startup.json');
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        
        if (data && data.status !== 'offline') {
            // Calculate session uptime
            const startTime = new Date(data.startup_time + 'Z');
            const sessionSeconds = Math.floor((new Date() - startTime) / 1000);
            
            uptimeElement.innerHTML = `<i class="fas fa-history me-1"></i>Session: ${formatUptime(sessionSeconds)}`;
        } else {
            // Bot is offline
            if (data && data.shutdown_time) {
                const shutdownTime = new Date(data.shutdown_time + 'Z');
                uptimeElement.innerHTML = 
                    '<i class="fas fa-power-off me-1"></i>Stopped: ' + 
                    formatUTCTime(shutdownTime);
            } else {
                uptimeElement.innerHTML = 
                    '<i class="fas fa-power-off me-1"></i>Status: Offline';
            }
        }
    } catch (error) {
        console.error('Error updating bot status:', error);
        uptimeElement.innerHTML = 
            '<i class="fas fa-exclamation-triangle me-1"></i>Status: Unknown';
    }
}

// Function to set active navigation item
function setActiveNavigation(currentPage) {
    // Remove active class from all nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // Add active class to current page
    const navElement = document.getElementById(`nav-${currentPage}`);
    if (navElement) {
        navElement.classList.add('active');
    }
}

// Initialize header functionality
function initializeHeader(currentPage) {
    // Set active navigation
    setActiveNavigation(currentPage);
    
    // Start clock updates
    setInterval(updateClock, 1000);
    updateClock();
    
    // Start bot status updates
    setInterval(updateBotStatus, 30000);
    updateBotStatus();
}
