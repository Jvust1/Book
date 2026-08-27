import { Link } from 'react-router-dom'

export interface SourceLinkProps {
  courseId: string
  kind: string
  sourceId: string
  onNavigate?: () => void
}

export function SourceLink({ courseId, kind, sourceId, onNavigate }: SourceLinkProps) {
  return (
    <Link
      className="source-link"
      onClick={onNavigate}
      to={`/courses/${encodeURIComponent(courseId)}/sources/${encodeURIComponent(kind)}/${encodeURIComponent(sourceId)}`}
    >
      查看教材来源
    </Link>
  )
}
