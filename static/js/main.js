// Basic interactions: modals and smooth anchor scrolling

(function () {
  // Smooth scroll for in-page anchors
  const header = document.querySelector('header');
  const headerH = () => (header ? header.offsetHeight : 0);
  document.addEventListener('click', (e) => {
    const a = e.target.closest('a[href^="#"]');
    if (!a) return;
    const id = a.getAttribute('href');
    if (!id || id === '#' || id.length < 2) return;
    const target = document.querySelector(id);
    if (!target) return;
    e.preventDefault();
    const y = target.getBoundingClientRect().top + window.pageYOffset - headerH() - 8; // small offset
    window.scrollTo({ top: y, behavior: 'smooth' });
  });

  // Modals: open/close
  function openModal(sel) {
    const el = typeof sel === 'string' ? document.querySelector(sel) : sel;
    if (!el) return;
    el.classList.remove('hidden');
    el.classList.add('flex');
    document.body.style.overflow = 'hidden';
  }
  function closeModal(el) {
    if (!el) return;
    el.classList.add('hidden');
    el.classList.remove('flex');
    document.body.style.overflow = '';
  }

  // Open by data-open-modal="#id"
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-open-modal]');
    if (!btn) return;
    const sel = btn.getAttribute('data-open-modal');
    if (sel) openModal(sel);
  });

  // Close buttons inside modal (data-close-modal)
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-close-modal]');
    if (!btn) return;
    const modal = btn.closest('.fixed.inset-0');
    closeModal(modal);
  });

  // Close on overlay click
  document.addEventListener('mousedown', (e) => {
    const overlay = e.target.closest('.fixed.inset-0');
    if (!overlay) return;
    // if clicked directly on overlay (not dialog content)
    const dialog = overlay.querySelector('.w-full.max-w-md');
    if (dialog && !dialog.contains(e.target)) {
      closeModal(overlay);
    }
  });

  // ESC to close topmost modal
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    const open = document.querySelector('.fixed.inset-0.flex');
    if (open) closeModal(open);
  });
})();

document.addEventListener('DOMContentLoaded', () => {
  // Simple before/after slider without external lib
  document.querySelectorAll('.before-after').forEach(wrapper => {
    const imgs = wrapper.querySelectorAll('img');
    const before = imgs[0];
    const after = wrapper.querySelector('[data-after]');
    // Adopt AFTER photo aspect ratio for the wrapper
    function applyAspectFromAfter() {
      if (!after || !after.naturalWidth || !after.naturalHeight) return;
      const w = after.naturalWidth;
      const h = after.naturalHeight;
      // Use CSS aspect-ratio when available
      wrapper.style.aspectRatio = `${w} / ${h}`;
      // Fallback for older browsers: set explicit height based on current width
      const setHeight = () => {
        const width = wrapper.clientWidth || wrapper.offsetWidth;
        if (width) wrapper.style.height = `${(h / w) * width}px`;
      };
      setHeight();
      window.addEventListener('resize', setHeight);
      // Ensure contained images fill the wrapper height
      [before, after].forEach(img => { if (img) { img.style.height = '100%'; img.style.width = '100%'; img.style.objectFit = 'cover'; } });
    }
    if (after && after.complete) applyAspectFromAfter();
    else if (after) after.addEventListener('load', applyAspectFromAfter);
    const slider = document.createElement('div');
    slider.className = 'ba-slider';
    const handle = document.createElement('div');
    handle.className = 'ba-handle';
    slider.appendChild(handle);
    wrapper.appendChild(slider);

    function setPos(x) {
      const rect = wrapper.getBoundingClientRect();
      const pos = Math.max(0, Math.min(x - rect.left, rect.width));
      const pct = (pos / rect.width) * 100;
      // Reveal AFTER on the right side (left = BEFORE, right = AFTER)
      after.style.clipPath = `inset(0 0 0 ${pct}%)`;
      handle.style.left = `${pct}%`;
      wrapper.style.setProperty('--ba-x', `${pct}%`);
    }

    setPos(wrapper.getBoundingClientRect().left + wrapper.clientWidth / 2);

    let dragging = false;
    ['mousedown','touchstart'].forEach(ev => slider.addEventListener(ev, () => dragging = true));
    ['mouseup','mouseleave','touchend'].forEach(ev => wrapper.addEventListener(ev, () => dragging = false));
    wrapper.addEventListener('mousemove', e => dragging && setPos(e.clientX));
    wrapper.addEventListener('touchmove', e => dragging && setPos(e.touches[0].clientX));
  });

  // Catalog filter
  const tags = document.querySelectorAll('.tag');
  const cards = document.querySelectorAll('#catalog-grid .card');
  tags.forEach(t => t.addEventListener('click', () => {
    tags.forEach(x => x.classList.remove('active'));
    t.classList.add('active');
    const f = t.dataset.filter;
    cards.forEach(c => {
      c.style.display = (f === 'all' || c.dataset.cat === f) ? '' : 'none';
    });
  }));

  function applyCatalogFilter(filter) {
    const btn = Array.from(tags).find(x => x.dataset.filter === filter);
    (btn || Array.from(tags).find(x => x.dataset.filter === 'all'))?.click();
  }

  // Clickable hero slides
  document.querySelectorAll('#hero-swiper .swiper-slide[data-filter]').forEach(slide => {
    slide.addEventListener('click', (e) => {
      const filter = slide.getAttribute('data-filter');
      const target = document.querySelector('#catalog');
      if (target) {
        const y = target.getBoundingClientRect().top + window.pageYOffset - (document.querySelector('header')?.offsetHeight || 0) - 8;
        window.scrollTo({ top: y, behavior: 'smooth' });
      }
      if (filter) applyCatalogFilter(filter);
    });
  });

  // YouTube lazy preview with thumbnail
  document.querySelectorAll('.yt').forEach(box => {
    const id = box.dataset.ytid;
    const nice = box.dataset.ytnice;
    const img = new Image();
    img.src = `https://i.ytimg.com/vi/${id}/maxresdefault.jpg`;
    img.onerror = () => {
      // Fallback to HQ; if HQ also fails, load iframe immediately
      img.onerror = () => { loadIframe(); };
      img.src = `https://i.ytimg.com/vi/${id}/hqdefault.jpg`;
    };
    img.alt = 'Видео превью';
    img.loading = 'lazy';
    img.className = 'yt-thumb';
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'yt-play';
    btn.setAttribute('aria-label', 'Смотреть видео');
    box.appendChild(img);
    box.appendChild(btn);
    function loadIframe() {
      const iframe = document.createElement('iframe');
      iframe.src = `https://www.youtube-nocookie.com/embed/${id}?autoplay=1&rel=0&controls=1&modestbranding=1&playsinline=1`;
      iframe.title = 'YouTube video';
      iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
      iframe.setAttribute('playsinline', '1');
      iframe.allowFullscreen = true;
      iframe.frameBorder = '0';
      box.innerHTML = '';
      box.appendChild(iframe);
    }
    // Load on any click inside the box
    btn.addEventListener('click', loadIframe);
    img.addEventListener('click', loadIframe);
    box.addEventListener('click', (e) => {
      // avoid double-trigger if already iframe
      if (box.querySelector('iframe')) return;
      loadIframe();
    });
    // Ensure button visible even if image fails to load
    let ready = false;
    img.onload = () => { ready = true; };
    setTimeout(() => {
      // If after 1500ms нет картинки, всё равно показываем кнопку
      if (!ready) {
        btn.style.opacity = '1';
      }
    }, 1500);
    // Keyboard accessibility
    box.tabIndex = 0;
    box.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        loadIframe();
      }
    });
  });

  // Auto-fill product name into consult modal
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-open-modal][data-product]');
    if (!btn) return;
    const prod = btn.getAttribute('data-product') || '';
    const modal = document.querySelector('#modal-consult');
    if (!modal) return;
    const comment = modal.querySelector('textarea[name="comment"]');
    if (comment) {
      const base = comment.getAttribute('data-base') || 'Консультация по:';
      comment.value = `${base} ${prod}`.trim();
    }
  });

  // Photo lightbox for completed projects
  document.addEventListener('click', (e) => {
    const a = e.target.closest('a[data-open-modal="#modal-photo"][data-photo]');
    if (!a) return;
    e.preventDefault();
    const src = a.getAttribute('data-photo');
    const alt = a.getAttribute('data-alt') || '';
    const modal = document.querySelector('#modal-photo');
    if (!modal) return;
    const img = modal.querySelector('img');
    if (img) { img.src = src; img.alt = alt; }
    // open via existing modal system
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    document.body.style.overflow = 'hidden';
  });

  // Quick contact floating panel toggle with CSS-driven animations
  (function(){
    const root = document.querySelector('[data-quick-root]');
    if (!root) return;
    const toggle = root.querySelector('[data-quick-toggle]');
    const panel = root.querySelector('[data-quick-panel]');
    if (!toggle || !panel) return;
    function open(){ root.classList.add('open'); toggle.setAttribute('aria-expanded','true'); }
    function close(){ root.classList.remove('open'); toggle.setAttribute('aria-expanded','false'); }
    function isOpen(){ return root.classList.contains('open'); }
    // init closed
    close();
    toggle.addEventListener('click', (e) => {
      e.stopPropagation();
      isOpen() ? close() : open();
    });
    document.addEventListener('click', (e) => {
      if (!isOpen()) return;
      if (root.contains(e.target)) return; // clicks inside do nothing
      close();
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && isOpen()) close();
    });
  })();

  // Swiper sliders (hero and reviews)
  try {
    if (window.Swiper) {
      const heroEl = document.querySelector('#hero-swiper');
      if (heroEl) {
        const heroSwiper = new Swiper(heroEl, {
          loop: false,
          slidesPerView: 1,
          preloadImages: true,
          updateOnImagesReady: true,
          observer: true,
          observeParents: true,
          autoplay: { delay: 3500, disableOnInteraction: false },
          pagination: { el: heroEl.querySelector('.swiper-pagination'), clickable: true },
        });
        heroEl.querySelectorAll('img').forEach(img => {
          if (img.complete) return;
          img.addEventListener('load', () => heroSwiper.update());
          img.addEventListener('error', () => heroSwiper.update());
        });
      }
      const revEl = document.querySelector('#reviews-swiper');
      let reviewsSwiper = null;
      function setupReviews(){
        if (!revEl) return;
        const isDesktop = window.innerWidth >= 1024;
        if (isDesktop) {
          if (reviewsSwiper && typeof reviewsSwiper.destroy === 'function') {
            reviewsSwiper.destroy(true, true);
            reviewsSwiper = null;
          }
          revEl.classList.add('reviews-grid');
        } else {
          revEl.classList.remove('reviews-grid');
          if (!reviewsSwiper && window.Swiper) {
            reviewsSwiper = new Swiper(revEl, {
              loop: true,
              spaceBetween: 16,
              autoplay: { delay: 4500, disableOnInteraction: false },
              pagination: { el: revEl.querySelector('.swiper-pagination'), clickable: true },
              slidesPerView: 1,
              breakpoints: {
                768: { slidesPerView: 2 },
              },
            });
          }
        }
      }
      if (revEl) {
        setupReviews();
        // Re-evaluate on resize (debounced)
        let rto;
        window.addEventListener('resize', () => {
          clearTimeout(rto);
          rto = setTimeout(setupReviews, 150);
        });
      }
    }
  } catch (_) { /* no-op */ }
});

// Minimal ripple effect for buttons/links
(function(){
  function addRipple(e){
    const target = e.target.closest('.btn-primary, .btn-outline, .btn-cta, [data-quick-panel] > a, .btn-primary-glow');
    if (!target) return;
    const rect = target.getBoundingClientRect();
    const ripple = document.createElement('span');
    ripple.className = 'ripple';
    const size = Math.max(rect.width, rect.height) * 1.2;
    const x = e.clientX - rect.left - size / 2;
    const y = e.clientY - rect.top - size / 2;
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';
    target.appendChild(ripple);
    ripple.addEventListener('animationend', () => ripple.remove());
  }
  document.addEventListener('click', addRipple);
})();
