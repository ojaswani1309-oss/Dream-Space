(function () {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  // sidebar (mobile)
  const sb = $('#sidebar'), ov = $('#overlay'), mb = $('#menuBtn');
  const toggle = (open) => { if (!sb) return; sb.classList.toggle('open', open); ov.classList.toggle('show', open); };
  if (mb) mb.addEventListener('click', () => toggle(!sb.classList.contains('open')));
  if (ov) ov.addEventListener('click', () => toggle(false));

  // progress bars animate in
  requestAnimationFrame(() => setTimeout(() => $$('[data-progress]').forEach(el => el.style.width = el.dataset.progress + '%'), 120));

  // toasts
  $$('.toast').forEach((t, i) => {
    const close = () => { t.classList.add('out'); setTimeout(() => t.remove(), 400); };
    $('.toast-x', t).addEventListener('click', close);
    setTimeout(close, 5000 + i * 800);
  });

  // confirm before destructive forms
  document.addEventListener('submit', (e) => {
    const msg = e.target.dataset && e.target.dataset.confirm;
    if (msg && !confirm(msg)) e.preventDefault();
  });

  // modal (journal entries)
  const modal = $('#modal'), body = $('#modalBody');
  const openModal = (tplId) => {
    const tpl = document.getElementById(tplId);
    if (!tpl) return;
    body.innerHTML = ''; body.appendChild(tpl.content.cloneNode(true));
    modal.classList.add('open'); modal.setAttribute('aria-hidden', 'false');
  };
  const closeModal = () => { modal.classList.remove('open'); modal.setAttribute('aria-hidden', 'true'); };
  if (modal) {
    $$('[data-modal]').forEach(c => {
      c.addEventListener('click', () => openModal(c.dataset.modal));
      c.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openModal(c.dataset.modal); } });
    });
    $('#modalX').addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => { if (e.target === modal) closeModal(); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') { closeModal(); toggle(false); } });
  }

  // music player bar
  const player = $('#player');
  if (player) {
    $$('.play').forEach(b => b.addEventListener('click', () => {
      $('#npTitle').textContent = b.dataset.title; $('#npArtist').textContent = b.dataset.artist;
      $('#npLink').href = b.dataset.url; player.hidden = false;
      window.open(b.dataset.url, '_blank', 'noopener');
    }));
    $('#npClose').addEventListener('click', () => player.hidden = true);
  }

  // goal slider live label
  $$('input.range').forEach(r => r.addEventListener('input', () => {
    const lab = r.closest('form').querySelector('.pct-label b'); if (lab) lab.textContent = r.value;
  }));

  // smooth page transitions
  document.addEventListener('click', (e) => {
    const a = e.target.closest('a[href]');
    if (!a || e.ctrlKey || e.metaKey || e.shiftKey || a.target === '_blank') return;
    const url = new URL(a.href, location.href);
    if (url.origin !== location.origin || (url.pathname === location.pathname && url.hash)) return;
    e.preventDefault(); document.body.classList.add('leaving');
    setTimeout(() => location.href = a.href, 170);
  });
  window.addEventListener('pageshow', () => document.body.classList.remove('leaving'));

  // browser notifications for today's reminders (if enabled in Settings)
  const en = $('#enableNotif');
  if (en) en.addEventListener('click', () => {
    if (!('Notification' in window)) return alert('Your browser does not support notifications.');
    Notification.requestPermission().then(p => alert(p === 'granted' ? 'Notifications allowed 💙 Remember to turn on "Browser notifications" and save.' : 'Notifications were not allowed.'));
  });
  const dataEl = document.getElementById('reminder-data');
  if (dataEl && 'Notification' in window) {
    const items = JSON.parse(dataEl.textContent || '[]');
    const fired = JSON.parse(sessionStorage.getItem('firedReminders') || '[]');
    const check = () => {
      if (Notification.permission !== 'granted') return;
      const now = new Date(), hm = String(now.getHours()).padStart(2, '0') + ':' + String(now.getMinutes()).padStart(2, '0');
      items.forEach(r => { if (r.time <= hm && !fired.includes(r.id)) {
        new Notification('Dream Space ⏰', { body: r.title }); fired.push(r.id); sessionStorage.setItem('firedReminders', JSON.stringify(fired)); } });
    };
    if (items.length) { check(); setInterval(check, 30000); }
  }
})();
