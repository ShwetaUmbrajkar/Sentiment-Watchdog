document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.getElementById('themeToggle');
    const body = document.body;

    // Load saved theme
    if (localStorage.getItem('theme') === 'dark') {
        body.setAttribute('data-theme', 'dark');
        toggle.checked = true;
    }

    // Toggle theme
    toggle.addEventListener('change', () => {
        if (toggle.checked) {
            body.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        } else {
            body.removeAttribute('data-theme');
            localStorage.setItem('theme', 'light');
        }
    });
});