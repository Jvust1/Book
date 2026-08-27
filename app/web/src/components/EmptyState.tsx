export function EmptyState({ message }: { message: string }) {
  return (
    <div className="empty-state" role="status">
      <p>{message}</p>
    </div>
  )
}
