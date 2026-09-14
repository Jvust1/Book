import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import { Icon } from './Icon'
import { useRecorder } from '../state/recorder'

export function AppShell() {
  const recording = useRecorder()
  const location = useLocation()
  const active = recording.status === 'recording' || recording.status === 'paused'
  return (
    <div className="app-shell">
      <header className="app-header">
        <Link className="app-brand" to="/">
          <span className="brand-symbol"><Icon name="book" /></span><span>Book <small>学习</small></span>
        </Link>
        <nav className="app-nav" aria-label="主导航">
          <NavLink to="/" end><Icon name="book" />教材库</NavLink>
          <NavLink to="/recording"><Icon name="mic" />课堂录音{active ? <span className="nav-recording-dot" /> : null}</NavLink>
          <NavLink to="/knowledge-base"><Icon name="grid" />知识库</NavLink>
          <NavLink to="/sync"><Icon name="download" />同步</NavLink>
        </nav>
        <span className="app-phase"><i />本地学习空间</span>
      </header>
      <main className="app-main">
        {active && location.pathname !== '/recording' ? <Link to="/recording" className="ongoing-recording"><span className="recording-dot is-live" />{recording.status === 'paused' ? '录音已暂停' : '正在录音'} · {recording.name}<span>返回控制 →</span></Link> : null}
        <Outlet />
      </main>
    </div>
  )
}
