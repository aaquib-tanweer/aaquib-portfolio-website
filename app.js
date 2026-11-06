'use strict';
// Add verified profile links and email here when ready.
const profile = { email: 'aaquibtanweer@icloud.com', github: 'https://github.com/aaquib-tanweer', linkedin: '', twitter: 'https://x.com/aaquib_tanweer' };
const main = document.querySelector('main');
const feed = document.querySelector('.retro-scrollbar');
const restore = document.querySelector('#restore-window');
const toast = document.querySelector('#toast');
let toastTimer;
function notify(message) {
  toast.textContent = message;
  toast.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toast.hidden = true; }, 4500);
}
function reveal() { main.hidden = false; restore.hidden = true; }
function jump(id) {
  reveal();
  setMobileView(id);
  const section = document.querySelector(id);
  if (!section) return;
  if (matchMedia('(max-width: 767px)').matches) window.scrollTo({top: 0, behavior: 'instant'});
  else section.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'start' });
  const link = document.querySelector(`aside a[href="${id}"]`);
  if (link && link.textContent.includes('#')) {
    document.querySelectorAll('aside a').forEach(a => { a.classList.remove('nav-active'); a.removeAttribute('aria-current'); });
    link.classList.add('nav-active'); link.setAttribute('aria-current', 'location');
    document.querySelector('section > div:first-child > div:first-child > span:first-child').textContent = link.querySelector('span').textContent;
  }
}
document.querySelectorAll('a[href^="#"]').forEach(link => link.addEventListener('click', event => {
  if (!link.getAttribute('href').startsWith('#')) return;
  event.preventDefault();
  if (link.dataset.unconfigured) return notify(`${link.dataset.unconfigured} hasn't been added yet.`);
  jump(link.getAttribute('href'));
}));
const toolbar = [...document.querySelectorAll('nav[aria-label="Window Toolbar"] button')];
toolbar[0].addEventListener('click', async () => {
  try {
    if (navigator.share) await navigator.share({ title: document.title, url: location.href });
    else { await navigator.clipboard.writeText(location.href); notify('Portfolio link copied.'); }
  } catch (error) { if (error.name !== 'AbortError') notify('Copy the page URL from your address bar to share it.'); }
});
toolbar[1].addEventListener('click', () => {
  location.href = `mailto:${profile.email}?subject=${encodeURIComponent('Hello from your portfolio')}`;
});
document.querySelectorAll('[aria-label="Close window"], [aria-label="Minimize window"]').forEach(button => button.addEventListener('click', () => { main.hidden = true; restore.hidden = false; restore.focus(); }));
restore.addEventListener('click', reveal);
document.querySelectorAll('[aria-label="Zoom window"], [aria-label="Window resize icon"]').forEach(button => button.addEventListener('click', () => { main.classList.toggle('zoomed'); fitDesktopWindow(); }));
document.querySelector('[aria-label="Pinned items"]').addEventListener('click', () => jump('#projects-section'));
document.querySelector('[aria-label="Preferences"]').addEventListener('click', () => notify('System 7 Cream · Your portfolio’s classic desktop theme.'));
const star = document.querySelector('[aria-label="Add to favorites"]');
function setStar(value) { star.setAttribute('aria-pressed', String(value)); star.querySelector('i').className = value ? 'fa-solid fa-star' : 'fa-regular fa-star'; }
try { setStar(localStorage.getItem('portfolio-starred') === 'true'); } catch { setStar(false); }
star.addEventListener('click', () => { const value = star.getAttribute('aria-pressed') !== 'true'; setStar(value); try { localStorage.setItem('portfolio-starred', String(value)); } catch {} notify(value ? 'Portfolio starred on this device.' : 'Removed from starred.'); });
document.querySelectorAll('#projects-section button').forEach(button => { button.disabled = true; button.title = 'Placeholder project — add your project URL to enable'; button.classList.add('opacity-50', 'cursor-not-allowed'); });
const form = document.querySelector('#contact-form');
const input = document.querySelector('#chat-input');
const help = document.querySelector('#contact-help');
help.hidden = false;
help.hidden = !profile.email;
form.querySelector('button span').textContent = profile.email ? 'Open Email' : 'Save Draft';
try { input.value = localStorage.getItem('portfolio-message-draft') || ''; } catch {}
form.addEventListener('submit', event => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message) { input.focus(); notify('Write a message first.'); return; }
  if (profile.email) location.href = `mailto:${profile.email}?subject=${encodeURIComponent('Hello from your portfolio')}&body=${encodeURIComponent(message)}`;
  else { try { localStorage.setItem('portfolio-message-draft', message); notify('Draft saved on this device. It has not been sent.'); } catch { notify('Your browser could not save this draft. Copy it to keep it.'); } }
});
document.querySelectorAll('[data-unconfigured]').forEach(link => {
  const key = ({ 'GitHub profile': 'github', 'LinkedIn profile': 'linkedin', 'Email address': 'email' })[link.dataset.unconfigured];
  if (profile[key]) { link.href = key === 'email' ? `mailto:${profile[key]}` : profile[key]; delete link.dataset.unconfigured; }
});
// Finder's location card is part of the desktop, independent of the feed.
const finderWindow = document.createElement('dialog');
finderWindow.className = 'finder-window';
finderWindow.setAttribute('aria-labelledby', 'finder-location-title');
finderWindow.innerHTML = `
  <header class="finder-titlebar">
    <button class="finder-close" type="button" aria-label="Close Finder">×</button>
    <span>Finder.app — Location</span>
    <span aria-hidden="true">▧</span>
  </header>
  <div class="finder-path">⌂ &nbsp; Aaquib / Current location</div>
  <div class="finder-content">
    <div class="finder-port"><span aria-hidden="true">⌖</span><span>Current port of call</span><span class="finder-dot" aria-hidden="true"></span></div>
    <div class="finder-city-art" aria-hidden="true">
      <svg viewBox="0 0 400 128" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M0 101H400M0 108H400M12 119H60M76 119H145M162 119H211M229 119H296M315 119H388"/>
        <path d="M18 96H382M48 95V45H68V95M332 95V45H352V95M44 45H72M328 45H356M48 54H68M332 54H352"/>
        <path d="M18 90L58 45L200 79L342 45L382 90M58 45L200 90L342 45M86 53V95M116 60V95M145 67V95M174 74V95M226 74V95M255 67V95M284 60V95M314 53V95"/>
        <path d="M102 97V83H115M125 97V78H139M265 97V82H278M288 97V86H303"/>
        <circle cx="200" cy="30" r="14" class="finder-sun"/>
        <path d="M142 22L149 18L156 22M235 17L242 13L249 17"/>
      </svg>
    </div>
    <p class="finder-eyebrow">HOME BASE / 001</p>
    <h2 id="finder-location-title">Kolkata<span aria-hidden="true">.</span></h2>
    <p class="finder-description">Currently living in Kolkata, India.</p>
    <div class="finder-details"><span>West Bengal, India</span><span id="finder-local-time"></span></div>
  </div>
  <footer class="finder-status"><span><span class="finder-dot" aria-hidden="true"></span> Location found</span><span>HOME_PORT.DAT</span></footer>`;
document.body.append(finderWindow);
finderWindow.querySelector('.finder-close').addEventListener('click', () => finderWindow.close());
finderWindow.addEventListener('click', event => {
  const rect = finderWindow.getBoundingClientRect();
  if (event.target === finderWindow && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom)) finderWindow.close();
});
function openFinder() {
  finderWindow.querySelector('#finder-local-time').textContent = new Intl.DateTimeFormat('en-IN', {timeZone:'Asia/Kolkata',hour:'2-digit',minute:'2-digit',hour12:true}).format(new Date()).toUpperCase() + ' IST';
  if (!finderWindow.open) finderWindow.showModal();
}
document.querySelectorAll('[data-purpose="desktop-shortcuts"] > div').forEach((icon, index) => {
  icon.setAttribute('role', 'button'); icon.tabIndex = 0;
  const action = () => { if (index === 0) openFinder(); else if (index === 3) jump('#projects-section'); else if (index === 5) notify('Trash is empty. A fresh start.'); else if (index === 4) notify('Portfolio OS v1.0 · Local edition'); else jump('#about-section'); };
  icon.addEventListener('click', action); icon.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); action(); } });
});

document.querySelector('aside button').addEventListener('click', () => notify('Portfolio OS v1.0 · Aaquib Tanweer’s workspace'));

// Mobile uses the same portfolio content, presented as compact app pages.
const mobileMenuToggle = document.querySelector('#mobile-menu-toggle');
function closeMobileMenu() {
  main.classList.remove('mobile-menu-open');
  mobileMenuToggle.setAttribute('aria-expanded', 'false');
  mobileMenuToggle.setAttribute('aria-label', 'Open navigation menu');
}
function setMobileView(id) {
  main.dataset.mobileView = id.slice(1);
  document.querySelectorAll('.mobile-bottom-nav a').forEach(link => {
    if (link.getAttribute('href') === id) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  });
  closeMobileMenu();
  if (matchMedia('(max-width: 767px)').matches) {
    feed.scrollTop = 0;
    const labels = {'#about-section':'about-me','#projects-section':'projects','#history-section':'work-history','#contact-section':'contact'};
    document.querySelector('section > div:first-child > div:first-child > span:first-child').textContent = '# ' + (labels[id] || 'about-me');
  }
}
mobileMenuToggle.addEventListener('click', () => {
  const open = main.classList.toggle('mobile-menu-open');
  mobileMenuToggle.setAttribute('aria-expanded', String(open));
  mobileMenuToggle.setAttribute('aria-label', open ? 'Close navigation menu' : 'Open navigation menu');
});
document.addEventListener('keydown', event => { if (event.key === 'Escape') closeMobileMenu(); });

document.querySelector('#mobile-finder').addEventListener('click', () => { closeMobileMenu(); openFinder(); });
document.querySelector('#mobile-share').addEventListener('click', () => { closeMobileMenu(); toolbar[0].click(); });

// Fit one complete desktop canvas uniformly; never crop a full-size hero into a short window.
const desktopStage = document.querySelector('#desktop-stage');
function fitDesktopWindow() {
  if (!matchMedia('(min-width: 768px)').matches) { desktopStage.style.removeProperty('--desktop-scale'); desktopStage.style.removeProperty('--desktop-height'); return; }
  const widthScale = (document.documentElement.clientWidth - 48) / 1480;
  const scale = main.classList.contains('zoomed') ? Math.min(1.25, widthScale) : Math.min(1, widthScale, (window.innerHeight - 48) / 900);
  desktopStage.style.setProperty('--desktop-scale', String(Math.max(0.1, scale)));
  desktopStage.style.setProperty('--desktop-height', `${Math.max(900, (window.innerHeight - 48) / scale)}px`);
}
window.addEventListener('resize', fitDesktopWindow);
fitDesktopWindow();
