import { Link, Outlet } from 'react-router-dom'

export function AppShell() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <Link className="app-brand" to="/">
          Book 学习
        </Link>
        <span className="app-phase">本地教材学习</span>
        <Link className="header-action" to="/recording">课堂录音</Link>
        <Link className="header-action" to="/knowledge-base">知识库</Link>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  )
}
