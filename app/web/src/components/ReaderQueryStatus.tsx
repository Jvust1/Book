interface ReaderQueryStatusProps {
  hasData: boolean
  fetching: boolean
  fetchedAfterMount: boolean
  updatedAt: number
  failed: boolean
  refresh: () => void
  cancel: () => void
}
export function ReaderQueryStatus({ hasData, fetching, fetchedAfterMount, updatedAt, failed, refresh, cancel }: ReaderQueryStatusProps) {
  return <aside className="reader-query-status" aria-label="教材读取状态">
    {hasData ? <div>
      <p role={failed ? 'status' : undefined}>{failed ? '网络中断，当前显示本次会话缓存；内容可能已更新。'
        : fetching ? '正在重新读取，当前显示本次会话缓存。'
        : !fetchedAfterMount ? '显示本次会话缓存。' : '读取完成，结果仅在本次页面会话内缓存。'}</p>
      <p className="secondary-text">最近读取：<time dateTime={new Date(updatedAt).toISOString()}>{new Date(updatedAt).toLocaleTimeString('zh-CN')}</time> · 刷新页面后清空</p>
    </div> : null}
    <div className="reader-query-actions">
      <button type="button" className="secondary-button" disabled={fetching} onClick={refresh}>重新读取</button>
      {fetching ? <button type="button" className="secondary-button" onClick={cancel}>取消读取</button> : null}
    </div>
  </aside>
}
