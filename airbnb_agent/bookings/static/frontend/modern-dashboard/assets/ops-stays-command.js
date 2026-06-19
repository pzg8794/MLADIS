(function () {
  const path = window.location.pathname.replace(/\/+$/, '');
  if (path !== '/ops/stays') return;

  const heroImage = '/static/frontend/modern-dashboard/stays/stay-6br.jpg';
  const modules = [
    ['Dashboard', 'Command overview and live metrics', '/ops/dashboard/', '#2563eb', '#dbeafe'],
    ['Reservations', 'Guest stays, channels, arrivals', '/ops/reservations/', '#0ea5e9', '#e0f2fe'],
    ['Calendar', 'Availability, blocks, pricing', '/ops/calendar/', '#7c3aed', '#ede9fe'],
    ['Stays', 'Listings, rooms, readiness', '/ops/stays/', '#0f766e', '#ccfbf1'],
    ['Maintenance', 'Issues, photos, repair status', '/ops/maintenance/', '#f97316', '#ffedd5'],
    ['Payments', 'Checkout status and providers', '/ops/payments/', '#0891b2', '#cffafe'],
    ['Deposits', 'Holds, captures, releases', '/ops/deposits/', '#e11d48', '#ffe4e6'],
    ['Reports', 'Revenue, occupancy, trends', '/ops/reports/', '#6d28d9', '#f3e8ff'],
    ['Agent Intelligence', 'AI suggestions and training', '/ops/agent/', '#0d9488', '#ccfbf1'],
    ['Listings', 'Properties and availability', '/ops/listings/', '#059669', '#d1fae5'],
    ['Customers', 'Profiles, consent, segments', '/ops/customers/', '#16a34a', '#dcfce7'],
    ['Tasks', 'Assigned jobs and completion', '/ops/workboard/', '#d97706', '#fef3c7'],
    ['Settings', 'Public site copy and identity', '/ops/settings/', '#475569', '#e2e8f0'],
    ['Users', 'Access, roles, operators', '/ops/admin/', '#1d4ed8', '#dbeafe'],
  ];

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function moduleMarkup() {
    return modules.map(([label, detail, href, tone, bg]) => `
      <a class="ops-stays-command-module" href="${escapeHtml(href)}" style="--module-tone: ${tone}; --module-bg: ${bg};">
        <span class="ops-stays-command-icon" aria-hidden="true"></span>
        <span><strong>${escapeHtml(label)}</strong><small>${escapeHtml(detail)}</small></span>
      </a>
    `).join('');
  }

  function renderCommandCenter() {
    const dashboardMain = document.querySelector('.dashboard-main');
    if (!dashboardMain) return false;

    const current = dashboardMain.querySelector('main.ops-stays-command-page, main.ops-page--stays, section.dashboard-error');
    if (current && current.getAttribute('data-ops-stays-command') === 'true') return true;

    const main = document.createElement('main');
    main.className = 'dashboard-content ops-page ops-page--stays ops-stays-command-page';
    main.setAttribute('data-ops-stays-command', 'true');
    main.innerHTML = `
      <section class="ops-stays-command-hero" aria-label="Admin command center">
        <div class="ops-stays-command-hero__copy">
          <h1>Admin command center ✨</h1>
          <p>Run the MLADIS operating system from one place: stays, reservations, guests, payments, deposits, reporting, users, settings, and connected services.</p>
          <div class="ops-stays-command-hero__actions">
            <a class="ops-stays-command-primary" href="/ops/dashboard/">Open all workspaces</a>
          </div>
        </div>
        <figure class="ops-stays-command-hero__media">
          <img src="${heroImage}" alt="MLADIS stay interior" loading="eager">
          <figcaption class="ops-stays-command-hero__chips">
            <span>System healthy</span>
            <span>Last sync: 2m ago</span>
            <span>All systems operational</span>
          </figcaption>
        </figure>
      </section>

      <section class="ops-stays-command-metrics" aria-label="Operational metrics">
        <article class="ops-stays-command-metric" style="--metric-swatch: #dbeafe; --metric-tone: #2563eb;"><span>Active stays</span><strong>128</strong><p>+12% vs yesterday</p></article>
        <article class="ops-stays-command-metric" style="--metric-swatch: #fef3c7; --metric-tone: #d97706;"><span>Pending requests</span><strong>23</strong><p>+5 new</p></article>
        <article class="ops-stays-command-metric" style="--metric-swatch: #dcfce7; --metric-tone: #16a34a;"><span>Deposit holds</span><strong>$74,560</strong><p>12 holds</p></article>
        <article class="ops-stays-command-metric" style="--metric-swatch: #ede9fe; --metric-tone: #7c3aed;"><span>Open tasks</span><strong>18</strong><p>3 completed</p></article>
      </section>

      <section class="ops-stays-command-grid" aria-label="Operations hub">
        <article class="ops-stays-command-panel">
          <header class="ops-stays-command-panel__heading">
            <div>
              <span class="ops-stays-command-panel__eyebrow">Command center</span>
              <h2>Main operations hub</h2>
              <p>Open any workspace without leaving the admin command center.</p>
            </div>
          </header>
          <div class="ops-stays-command-module-grid">${moduleMarkup()}</div>
        </article>

        <aside class="ops-stays-command-side" aria-label="Live operations">
          <article class="ops-stays-command-panel ops-stays-command-feed">
            <header class="ops-stays-command-panel__heading">
              <div>
                <span class="ops-stays-command-panel__eyebrow">Live operations feed</span>
                <h3>Recent activity</h3>
              </div>
            </header>
            <div class="ops-stays-command-feed-item" style="--feed-tone: #16a34a; --feed-bg: rgba(22, 163, 74, 0.13);"><i></i><div><strong>Reservation confirmed</strong><p>G-101 arrival window and deposit hold are aligned.</p></div><time>2m</time></div>
            <div class="ops-stays-command-feed-item" style="--feed-tone: #2563eb; --feed-bg: rgba(37, 99, 235, 0.13);"><i></i><div><strong>Calendar feed synced</strong><p>All property availability feeds refreshed successfully.</p></div><time>7m</time></div>
            <div class="ops-stays-command-feed-item" style="--feed-tone: #f97316; --feed-bg: rgba(249, 115, 22, 0.13);"><i></i><div><strong>Maintenance review queued</strong><p>Photo evidence is ready for the next work order.</p></div><time>18m</time></div>
            <div class="ops-stays-command-feed-item" style="--feed-tone: #7c3aed; --feed-bg: rgba(124, 58, 237, 0.13);"><i></i><div><strong>Agent answer updated</strong><p>FAQ training is ready for owner approval.</p></div><time>32m</time></div>
          </article>

          <article class="ops-stays-command-panel ops-stays-command-health">
            <header class="ops-stays-command-panel__heading">
              <div>
                <span class="ops-stays-command-panel__eyebrow">System health & access</span>
                <h3>Operational status</h3>
              </div>
            </header>
            <div class="ops-stays-command-health-row"><span>Booking APIs</span><span>Online</span></div>
            <div class="ops-stays-command-health-row"><span>Calendar feeds</span><span>Synced</span></div>
            <div class="ops-stays-command-health-row"><span>Payments</span><span>Ready</span></div>
            <div class="ops-stays-command-health-row" style="--health-tone: #7c2d12; --health-bg: #ffedd5;"><span>Owner access</span><span>Verified</span></div>
          </article>
        </aside>
      </section>
    `;

    if (current) {
      current.replaceWith(main);
    } else {
      dashboardMain.appendChild(main);
    }
    return true;
  }

  function scheduleRender() {
    window.requestAnimationFrame(renderCommandCenter);
  }

  scheduleRender();
  window.addEventListener('DOMContentLoaded', scheduleRender, { once: true });

  const observer = new MutationObserver(() => {
    if (!document.querySelector('main.ops-stays-command-page[data-ops-stays-command="true"]')) {
      scheduleRender();
    }
  });
  observer.observe(document.documentElement, { childList: true, subtree: true });
}());