import type { LearningMode } from '../api/types'

const MODES: readonly { mode: LearningMode; label: string }[] = [
  { mode: 'preview', label: '预习' },
  { mode: 'learn', label: '学习' },
  { mode: 'review', label: '复习' },
  { mode: 'practice', label: '刷题' },
]

export interface ModeTabsProps {
  mode: LearningMode
  onChange: (mode: LearningMode) => void
}

export function ModeTabs({ mode, onChange }: ModeTabsProps) {
  return (
    <div className="mode-tabs" role="tablist" aria-label="学习模式">
      {MODES.map((item) => (
        <button
          className="mode-tab"
          data-active={item.mode === mode ? 'true' : 'false'}
          key={item.mode}
          type="button"
          role="tab"
          aria-selected={item.mode === mode}
          onClick={() => onChange(item.mode)}
        >
          {item.label}
        </button>
      ))}
    </div>
  )
}
