'use strict';
function contentElement(tag, text, className) {
  const el = document.createElement(tag);
  if (text !== undefined) el.textContent = text;
  if (className) el.className = className;
  return el;
}
let contentRequest = 0;
async function loadPortfolio() {
  const request = ++contentRequest;
  try {
    const url = new URL(document.body.dataset.contentUrl, location.href);
    url.searchParams.set('v', Date.now().toString());
    const response = await fetch(url.href, {cache: 'no-store'});
    if (!response.ok) throw new Error('Content unavailable');
    const content = await response.json();
    if (request !== contentRequest) return;
    for (const field of ['bio', 'headline', 'skills', 'education']) document.querySelector(`#portfolio-${field}`).textContent = content[field];
    if (Array.isArray(content.expertise)) {
      const container = document.querySelector('#profile-expertise');
      if (container) {
        container.replaceChildren();
        content.expertise.forEach((focus, index) => {
          const card = contentElement('div', undefined, 'expertise-tile p-2.5 bg-os-panel/50 border border-os-border rounded');
          const icon = contentElement('i', undefined, 'credential-icon ' + (['fa-solid fa-server','fa-solid fa-microchip','fa-solid fa-wrench'][index] || 'fa-solid fa-code')); icon.setAttribute('aria-hidden', 'true');
          card.append(icon, contentElement('p', focus.title, 'font-bold uppercase text-[11px] text-neutral-600 mb-1'), contentElement('p', focus.technologies));
          if (focus.title === 'Systems & Networking' && focus.description) card.append(contentElement('p', focus.description, 'mt-2 leading-relaxed'));
          container.append(card);
        });
      }
    }
    const history = document.querySelector('#work-history');
    if (history && Array.isArray(content.experience)) {
      history.replaceChildren();
      for (const job of content.experience) {
        const card = contentElement('div', undefined, 'p-4 border-2 border-os-border rounded-lg bg-os-sidebar font-mono text-xs');
        const list = contentElement('ul', undefined, 'list-disc pl-4 space-y-1');
        for (const item of job.responsibilities || []) list.append(contentElement('li', item));
        card.append(contentElement('h3', `${job.role} · ${job.company}`, 'font-bold text-sm'), contentElement('p', `${job.period} · ${job.type}`, 'mt-1 mb-2'), list);
        history.append(card);
      }
    }
    document.querySelector('#project-count').textContent = `[${content.projects.length}]`;
    document.querySelector('#sidebar-project-count').textContent = content.projects.length;
    const projects = document.querySelector('#project-list');
    projects.replaceChildren();
    if (!content.projects.length) projects.append(contentElement('p', 'No projects yet. New experiments will appear here.', 'empty-state'));
    content.projects.forEach(project => {
      const card = contentElement('div', undefined, 'content-card');
      const heading = contentElement('h3');
      if (project.url && /^https?:\/\//i.test(project.url)) {
        const titleLink = contentElement('a', project.title, 'underline decoration-dotted underline-offset-4 hover:decoration-solid');
        titleLink.href = project.url; titleLink.target = '_blank'; titleLink.rel = 'noopener noreferrer';
        heading.append(titleLink);
      } else heading.textContent = project.title;
      card.append(heading, contentElement('p', project.preview));
      if (project.tags) card.append(contentElement('small', project.tags, 'font-mono'));
      if (project.url && /^https?:\/\//i.test(project.url)) {
        const link = contentElement('a', 'View Project ↗', 'editor-button');
        link.href = project.url; link.target = '_blank'; link.rel = 'noopener noreferrer'; card.append(link);
      } else card.append(contentElement('small', 'Placeholder · Project link not added yet', 'font-mono'));
      projects.append(card);
    });
  } catch {
    if (request !== contentRequest) return;
    document.querySelector('#project-list').replaceChildren(contentElement('p', 'Unable to load projects. Please refresh or try again later.', 'empty-state'));
  }
}
loadPortfolio();
// Refresh deployed content when returning to the page.
window.addEventListener('pageshow', event => { if (event.persisted) loadPortfolio(); });
document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') loadPortfolio(); });
