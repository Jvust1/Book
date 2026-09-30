import { useLayoutEffect, useRef, useState } from 'react'
import katex from 'katex'
import renderMathInElement from 'katex/contrib/auto-render'
import 'katex/dist/katex.min.css'

// Limits are presentation safeguards. Rejected input is always retained verbatim.
const MAX_TEXT_LENGTH = 100_000
const MAX_FORMULA_LENGTH = 16_384
const DELIMITERS = [
  { left: '$$', right: '$$', display: true },
  { left: '\\(', right: '\\)', display: false },
  { left: '\\[', right: '\\]', display: true },
]

function formulaBody(text: string): string {
  const trimmed = text.trim()
  for (const { left, right } of DELIMITERS) {
    if (trimmed.startsWith(left) && trimmed.endsWith(right)) {
      return trimmed.slice(left.length, -right.length)
    }
  }
  return text
}

interface MathContentProps {
  text: string
  formula?: boolean
  className?: string
}

/** Render only a fresh text node, never source HTML; React owns the outer shell. */
export function MathContent({ text, formula = false, className = '' }: MathContentProps) {
  const hostRef = useRef<HTMLSpanElement>(null)
  const [fallback, setFallback] = useState(false)

  useLayoutEffect(() => {
    const host = hostRef.current
    if (!host) return
    host.replaceChildren(document.createTextNode(text))
    let failed = false
    const options = {
      trust: false,
      strict: 'error' as const,
      throwOnError: true,
      output: 'htmlAndMathml' as const,
      maxExpand: 500,
      maxSize: 20,
      // Never share mutable macro definitions between cards, modes or sources.
      macros: {},
    }
    try {
      if (text.length > (formula ? MAX_FORMULA_LENGTH : MAX_TEXT_LENGTH)) {
        throw new Error('Math input exceeds the presentation budget')
      }
      if (formula) {
        katex.render(formulaBody(text), host, { ...options, displayMode: true })
      } else {
        renderMathInElement(host, {
          ...options,
          delimiters: DELIMITERS,
          preProcess(math) {
            if (math.length > MAX_FORMULA_LENGTH) {
              throw new Error('Math input exceeds the presentation budget')
            }
            return math
          },
          // Upstream retains a failed segment's original delimiters and text.
          errorCallback() { failed = true },
        })
      }
    } catch {
      // Error messages can contain source HTML. Never render them as markup.
      host.replaceChildren(document.createTextNode(text))
      failed = true
    }
    setFallback(failed)
  }, [formula, text])

  return (
    <div className={`math-content ${formula ? 'formula-block' : 'learning-content'} ${className}`}>
      <span ref={hostRef} className="math-content-host" />
      {fallback ? <span className="math-fallback-note">部分公式暂无法排版，已保留原文</span> : null}
      {formula && !fallback ? (
        <details className="math-source">
          <summary>查看公式原文</summary>
          <code>{text}</code>
        </details>
      ) : null}
    </div>
  )
}
