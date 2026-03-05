(() => {
  const menuToggle = document.getElementById('menu-toggle');
  const mobileNav = document.getElementById('mobile-nav');
  const bar1 = document.getElementById('bar1');
  const bar2 = document.getElementById('bar2');
  const bar3 = document.getElementById('bar3');
  const closers = document.querySelectorAll('[data-close-mobile-nav]');

  let menuOpen = false;

  const closeMobileNav = () => {
    if (!mobileNav) return;

    menuOpen = false;
    mobileNav.classList.add('opacity-0', 'pointer-events-none');
    mobileNav.classList.remove('opacity-100', 'pointer-events-auto');

    if (bar1) bar1.style.transform = '';
    if (bar2) bar2.style.opacity = '';
    if (bar3) {
      bar3.style.transform = '';
      bar3.style.width = '';
    }
    document.body.style.overflow = '';
  };

  if (menuToggle && mobileNav) {
    menuToggle.addEventListener('click', () => {
      menuOpen = !menuOpen;

      if (menuOpen) {
        mobileNav.classList.remove('opacity-0', 'pointer-events-none');
        mobileNav.classList.add('opacity-100', 'pointer-events-auto');
        if (bar1) bar1.style.transform = 'rotate(45deg) translateY(6px)';
        if (bar2) bar2.style.opacity = '0';
        if (bar3) {
          bar3.style.transform = 'rotate(-45deg) translateY(-6px)';
          bar3.style.width = '1.5rem';
        }
        document.body.style.overflow = 'hidden';
      } else {
        closeMobileNav();
      }
    });
  }

  closers.forEach((node) => node.addEventListener('click', closeMobileNav));

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-fade-in');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1 }
  );

  document.querySelectorAll('.scroll-reveal').forEach((el) => observer.observe(el));
})();
