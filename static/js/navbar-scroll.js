let lastScrollY = window.scrollY;
const nav = document.querySelector('nav');
let ticking = false;

window.addEventListener('scroll', () => {
    if (!nav) return;
    
    if (!ticking) {
        window.requestAnimationFrame(() => {
            const currentScrollY = window.scrollY;
            
            if (currentScrollY > lastScrollY && currentScrollY > 50) {
                nav.classList.add('nav-hidden');
            } 
            else if (currentScrollY < lastScrollY) {
                nav.classList.remove('nav-hidden');
            }
            
            lastScrollY = currentScrollY;
            ticking = false;
        });
        
        ticking = true;
    }
});