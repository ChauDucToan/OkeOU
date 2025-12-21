window.addEventListener('scroll', function() {
    const navbar = document.getElementById('navbar');
    if (window.scrollY > 50) {
        navbar.classList.add('navbar-scrolled');
        navbar.classList.remove('glass-effect');
    } else {
        navbar.classList.remove('navbar-scrolled');
        navbar.classList.add('glass-effect');
    }
});