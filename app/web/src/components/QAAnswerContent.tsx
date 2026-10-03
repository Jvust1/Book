import { memo } from 'react'
import Markdown, { type Components, type Options } from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import { MathContent } from './MathContent'

const MAX_MARKDOWN_LENGTH = 100_000
const plugins: Options['remarkPlugins'] = [remarkGfm, [remarkMath, { singleDollarTextMath: false }]]
const allowedElements = [
  'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'em', 'strong',
  'blockquote', 'pre', 'code', 'hr', 'br', 'del', 'table', 'thead', 'tbody',
  'tr', 'th', 'td', 'a', 'img', 'input', 'section', 'sup',
]
const components: Components = {
  h1: ({ children }) => <h2>{children}</h2>,
  // Model-authored URLs never become source authority or initiate resource loads.
  a: ({ children }) => <span className="qa-inert-link">{children}<small>（未核验链接）</small></span>,
  img: ({ alt }) => <span className="qa-inert-image">图片未加载{alt ? `：${alt}` : ''}</span>,
  input: ({ checked }) => <span role="img" aria-label={checked ? '已勾选条目' : '未勾选条目'}>{checked ? '☑' : '☐'}</span>,
  table: ({ children }) => <div className="qa-table-scroll"><table>{children}</table></div>,
  pre: ({ node, children }) => {
    const code = node?.children[0]
    if (code?.type === 'element' && code.tagName === 'code' &&
      Array.isArray(code.properties.className) && code.properties.className.includes('math-display')) {
      const text = code.children.map(child => child.type === 'text' ? child.value : '').join('').replace(/\n$/, '')
      return <MathContent text={text} formula />
    }
    return <pre>{children}</pre>
  },
  code: ({ className, children }) => {
    if (className?.split(' ').includes('math-inline')) {
      return <MathContent text={String(children)} formula inline />
    }
    return <code>{children}</code>
  },
}

/** Only presentation changes. The API-gated citation cards remain separate. */
export const QAAnswerContent = memo(function QAAnswerContent({ text }: { text: string }) {
  return (
    <div className="qa-answer-content">
      {text.length <= MAX_MARKDOWN_LENGTH ? (
        <div className="qa-markdown">
          <Markdown skipHtml allowedElements={allowedElements} components={components} remarkPlugins={plugins}>{text}</Markdown>
        </div>
      ) : <p className="learning-content">{text}</p>}
      <details className="qa-original-answer">
        <summary>查看回答原文</summary>
        <pre>{text}</pre>
      </details>
    </div>
  )
})
