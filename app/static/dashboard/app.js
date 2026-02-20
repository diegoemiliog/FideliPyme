/* === FideliPyme Dashboard - Global JS === */

// Sidebar toggle (mobile)
function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
    document.getElementById('sidebarOverlay').classList.toggle('open');
}

// Toast notifications
function showToast(message, type) {
    type = type || 'success';
    var toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = 'toast toast-' + type + ' visible';
    setTimeout(function() {
        toast.classList.remove('visible');
    }, 3000);
}
