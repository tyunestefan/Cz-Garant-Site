document.addEventListener('DOMContentLoaded', () => {
  // ---------- Мобильное / компактное меню (бургер) ----------
  const burger = document.getElementById('navBurger');
  const menu = document.getElementById('mobileMenu');

  if (burger && menu) {
    burger.addEventListener('click', () => {
      const isOpen = menu.classList.toggle('open');
      burger.classList.toggle('active', isOpen);
      burger.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });

    menu.querySelectorAll('a').forEach((link) => {
      link.addEventListener('click', () => {
        menu.classList.remove('open');
        burger.classList.remove('active');
        burger.setAttribute('aria-expanded', 'false');
      });
    });

    // Закрыть меню, если окно расширили обратно до полного десктопа
    window.addEventListener('resize', () => {
      if (window.innerWidth > 860) {
        menu.classList.remove('open');
        burger.classList.remove('active');
        burger.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // ---------- Появление блоков при скролле ----------
  const revealItems = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && revealItems.length) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('reveal-visible');
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15, rootMargin: '0px 0px -40px 0px' }
    );
    revealItems.forEach((el) => io.observe(el));
  } else {
    revealItems.forEach((el) => el.classList.add('reveal-visible'));
  }

  // ---------- Переливающийся градиент при скролле ----------
  let ticking = false;

  function updateScrollVar() {
    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const progress = docHeight > 0 ? scrollTop / docHeight : 0;
    document.documentElement.style.setProperty('--scroll', progress.toFixed(4));
    ticking = false;
  }

  window.addEventListener('scroll', () => {
    if (!ticking) {
      window.requestAnimationFrame(updateScrollVar);
      ticking = true;
    }
  });

  updateScrollVar();
});
