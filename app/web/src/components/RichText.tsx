import type { Components } from 'react-markdown'
import Markdown from 'react-markdown'
import katex from 'katex'
import rehypeKatex from 'rehype-katex'
import remarkBreaks from 'remark-breaks'
import remarkMath from 'remark-math'

import 'katex/dist/katex.min.css'

/**
 * Normalize the delimiters commonly emitted by textbook and ChatGPT content
 * to the dollar delimiters understood by remark-math. Keeping this at the
 * boundary means Chinese prose and inline/display formulas can be mixed
 * without requiring callers to escape every backslash a second time.
 */
export function normalizeMathDelimiters(value: string): string {
  // Code examples are literal text, including their backslashes and delimiters.
  return value.split(/(```[\s\S]*?```|~~~[\s\S]*?~~~|`[^`\n]+`)/g).map((part, index) => index % 2 ? part : part
    .replace(/\\\[([\s\S]*?)\\\]/g, (_, body: string) => `\n$$\n${body}\n$$\n`)
    .replace(/\\\(([\s\S]*?)\\\)/g, (_, body: string) => `$${body}$`)).join('')
}

const components: Components = {
  a: ({ href, children, ...props }) => (
    <a href={href} target="_blank" rel="noreferrer" {...props}>
      {children}
    </a>
  ),
}

export interface RichTextProps {
  content: string
  className?: string
}

/** Render trusted textbook prose with safe Markdown and KaTeX math output. */
export function RichText({ content, className = 'learning-content' }: RichTextProps) {
  return (
    <div className={`rich-text ${className}`}>
      <Markdown
        skipHtml
        disallowedElements={['img', 'iframe']}
        remarkPlugins={[remarkMath, remarkBreaks]}
        rehypePlugins={[[rehypeKatex, { output: 'htmlAndMathml', trust: false, maxExpand: 1000, maxSize: 20 }]]}
        components={components}
      >
        {normalizeMathDelimiters(content)}
      </Markdown>
    </div>
  )
}

export interface FormulaBlockProps {
  formula: string
}

/** Legacy formula fields use ^(1/p) for a grouped exponent; preserve that grouping in TeX. */
export function normalizeFormula(value: string): string {
  if (value.includes('\\')) return value
  let result = ''
  for (let i = 0; i < value.length; i++) {
    if ((value[i] === '^' || value[i] === '_') && value[i + 1] === '(') {
      let depth = 1, end = i + 2
      for (; end < value.length && depth; end++) {
        if (value[end] === '(') depth++
        if (value[end] === ')') depth--
      }
      if (!depth) { result += value[i] + '{' + normalizeFormula(value.slice(i + 2, end - 1)) + '}'; i = end - 1; continue }
    }
    result += value[i]
  }
  return result
}

/** Render a formula field as display math, even when the API omits delimiters. */
export function FormulaBlock({ formula }: FormulaBlockProps) {
  const value = formula.trim()
  const pair = [['$$', '$$'], ['\\[', '\\]'], ['\\(', '\\)'], ['$', '$']].find(([start, end]) => value.startsWith(start) && value.endsWith(end))
  const displayValue = pair ? value.slice(pair[0].length, -pair[1].length).trim() : value
  let html = ''
  try {
    html = katex.renderToString(normalizeFormula(displayValue), { displayMode: true, throwOnError: true, trust: false, maxExpand: 1000, maxSize: 20, output: 'html' })
  } catch {
    html = ''
  }
  return (
    <div className="formula-block" role="math" aria-label={value}>
      {html ? <span aria-hidden="true" dangerouslySetInnerHTML={{ __html: html }} /> : <code className="formula-fallback">{value}</code>}
      {html ? <span className="formula-source-text">{value}</span> : <p className="formula-error">该公式语法暂不支持，已保留原文。</p>}
    </div>
  )
}
