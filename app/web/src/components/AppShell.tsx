import { Link, Outlet } from 'react-router-dom'

export function AppShell() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <Link className="app-brand" to="/">
          Book 学习
        </Link>
        <span className="app-phase">本地教材学习</span>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  )
}
