import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { QAAnswerContent } from './QAAnswerContent'

describe('QAAnswerContent with real react-markdown and KaTeX', () => {
  it('renders structured explanations and retains the exact original answer', async () => {
    const text = '# 合成解答\n\n**步骤**\n\n1. 取数值\n2. 验证\n\n| 项目 | 数值 |\n| --- | --- |\n| x | 3 |\n\n```python\nx = 3\n```'
    const { container } = render(<QAAnswerContent text={text} />)
    expect(screen.getByRole('heading', { level: 2, name: '合成解答' })).toBeInTheDocument()
    expect(screen.getByRole('list')).toBeInTheDocument()
    expect(screen.getByRole('table')).toHaveTextContent('项目数值x3')
    expect(container.querySelector('.qa-markdown strong')).toHaveTextContent('步骤')
    expect(container.querySelector('.qa-markdown pre code')).toHaveTextContent('x = 3')
    await userEvent.click(screen.getByText('查看回答原文', { exact: true }))
    expect(container.querySelector('.qa-original-answer pre')?.textContent).toBe(text)
  })

  it('renders double-dollar inline/display math with accessible output while preserving currency', () => {
    const text = '价格 $5 与 $10；平方 $$x^2=9$$。\n\n$$\n\\frac{1}{2}\n$$'
    const { container } = render(<QAAnswerContent text={text} />)
    expect(container.querySelectorAll('.qa-markdown .katex')).toHaveLength(2)
    expect(container.querySelectorAll('.qa-markdown .katex-display')).toHaveLength(1)
    expect(container.querySelectorAll('.qa-markdown math')).toHaveLength(2)
    expect(container.querySelector('.qa-markdown p')).toHaveTextContent('价格 $5 与 $10；平方')
    expect(container.querySelector('.math-inline details')).toBeNull()
    expect(container.querySelector('p div')).toBeNull()
  })

  it('does not interpret math delimiters inside code fences', () => {
    const { container } = render(<QAAnswerContent text={'```text\n$$x^2$$\n```'} />)
    expect(container.querySelector('.qa-markdown .katex')).toBeNull()
    expect(container.querySelector('.qa-markdown code')).toHaveTextContent('$$x^2$$')
  })

  it('keeps Markdown links, images, raw HTML and unsafe math inactive', () => {
    const text = '[read](https://example.invalid/track)\n\n![plot](https://example.invalid/image.png)\n\n<script>alert(1)</script>\n\n<img src="https://example.invalid/secret">\n\n$$\\href{javascript:alert(1)}{click}$$'
    const { container } = render(<QAAnswerContent text={text} />)
    expect(container.querySelectorAll('a, img, script, iframe, style, form')).toHaveLength(0)
    expect(screen.getByText('图片未加载：plot')).toBeInTheDocument()
    expect(screen.getByText('（未核验链接）')).toBeInTheDocument()
    expect(container.querySelector('.qa-original-answer pre')?.textContent).toBe(text)
  })

  it('shows failed math as its source and does not leak macros into later answers', () => {
    const { container, rerender } = render(<QAAnswerContent text={String.raw`$$\gdef\foo{123}\foo$$`} />)
    expect(container.querySelector('.qa-markdown .katex')).not.toBeNull()
    rerender(<QAAnswerContent text={String.raw`$$\foo$$`} />)
    expect(container.querySelector('.qa-markdown .katex')).toBeNull()
    expect(container.querySelector('.qa-markdown')).toHaveTextContent(String.raw`\foo`)
    expect(container.querySelector('.qa-markdown')).toHaveTextContent('已保留原文')
  })

  it('renders task items as inert symbols and preserves strikethrough', () => {
    const { container } = render(<QAAnswerContent text={'- [x] 完成\n- [ ] 检查\n\n~~旧解释~~'} />)
    expect(container.querySelector('input')).toBeNull()
    expect(screen.getByRole('img', { name: '已勾选条目' })).toBeInTheDocument()
    expect(container.querySelector('del')).toHaveTextContent('旧解释')
  })

  it('falls back to complete plain text for oversized answers', () => {
    const text = '# ' + 'x'.repeat(100_001)
    const { container } = render(<QAAnswerContent text={text} />)
    expect(container.querySelector('.qa-markdown')).toBeNull()
    expect(container.querySelector('.learning-content')?.textContent).toBe(text)
  })
})
