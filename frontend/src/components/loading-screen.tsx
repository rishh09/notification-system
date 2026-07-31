export function LoadingScreen({ label = "Loading your workspace…" }) {
  return (
    <main className="loading-screen">
      <span className="brand-mark brand-mark-large">S</span>
      <div className="loading-bar" aria-hidden="true">
        <span />
      </div>
      <p>{label}</p>
    </main>
  );
}
