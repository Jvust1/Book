import { Link } from 'react-router-dom'

export interface SourceLinkProps {
  courseId: string
  kind: string
  sourceId: string
}

export function SourceLink({ courseId, kind, sourceId }: SourceLinkProps) {
  return (
    <Link
      className="source-link"
      to={`/courses/${encodeURIComponent(courseId)}/sources/${encodeURIComponent(kind)}/${encodeURIComponent(sourceId)}`}
    >
      查看教材来源
    </Link>
  )
}
