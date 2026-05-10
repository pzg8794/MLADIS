export function DashboardSkeleton() {
  return (
    <main className="dashboard-content" aria-label="Loading dashboard">
      <section className="hero-skeleton">
        <span />
        <strong />
        <p />
      </section>
      <section className="metric-grid">
        {['a', 'b', 'c', 'd'].map((item) => <article className="metric-card skeleton-card" key={item} />)}
      </section>
      <section className="dashboard-grid">
        <article className="dashboard-panel panel-large skeleton-card" />
        <article className="dashboard-panel skeleton-card" />
        <article className="dashboard-panel skeleton-card" />
      </section>
    </main>
  );
}
