import { StrictMode } from 'react'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { MathContent } from './MathContent'

describe('MathContent with real KaTeX', () => {
  it('renders a formula using accessible MathML and keeps the exact source', () => {
    const text = String.raw`\frac{1}{2} + x^2`
    const { container } = render(<MathContent text={text} formula />)
    expect(container.querySelector('.katex-display .katex')).not.toBeNull()
    expect(container.querySelector('math')).not.toBeNull()
    expect(container.querySelector('annotation')?.textContent).toBe(text)
    expect(container.querySelector('code')?.textContent).toBe(text)
    expect(screen.queryByText(/暂无法排版/)).not.toBeInTheDocument()
  })

  it.each([String.raw`\[x^2\]`, '$$x^2$$', String.raw`\(x^2\)`])(
    'accepts an already delimited formula: %s', (text) => {
      const { container } = render(<MathContent text={text} formula />)
      expect(container.querySelector('annotation')?.textContent).toBe('x^2')
      expect(container.querySelector('code')?.textContent).toBe(text)
    },
  )

  it('uses upstream delimiter parsing for mixed Chinese prose and math', () => {
    const text = String.raw`设 \(x=2\)，因此 \[x^2=4\]。`
    const { container } = render(<MathContent text={text} />)
    expect(container.querySelectorAll('.katex')).toHaveLength(2)
    expect(container.querySelectorAll('.katex-display')).toHaveLength(1)
    expect(container.textContent).toContain('设 ')
    expect(container.textContent).toContain('，因此 ')
  })

  it('does not turn currency, unmatched delimiters or HTML into markup', () => {
    const text = String.raw`$5 and $10; \(unclosed; <img src=x onerror=alert(1)>`
    const { container } = render(<MathContent text={text} />)
    expect(container.querySelector('.math-content-host')?.textContent).toBe(text)
    expect(container.querySelectorAll('img, script, .katex')).toHaveLength(0)
  })

  it('retains invalid math segments without hiding valid neighboring content', () => {
    const text = String.raw`前文 \(\badcommand{x}\) 中间 \(x=2\) 后文`
    const { container } = render(<MathContent text={text} />)
    expect(container.querySelector('.math-content-host')?.textContent).toContain(String.raw`\(\badcommand{x}\)`)
    expect(container.querySelectorAll('.katex')).toHaveLength(1)
    expect(screen.getByText(/已保留原文/)).toBeInTheDocument()
  })

  it.each([
    String.raw`\href{javascript:alert(1)}{click}`,
    String.raw`\includegraphics{https://example.invalid/track.png}`,
    String.raw`\htmlClass{injected}{x}`,
  ])('does not create links, images or arbitrary HTML for %s', (text) => {
    const { container } = render(<MathContent text={text} formula />)
    expect(container.querySelectorAll('a, img, script, .injected')).toHaveLength(0)
  })

  it('bounds recursive macros and retains source safely', () => {
    const text = String.raw`\def\loop{\loop}\loop`
    const { container } = render(<MathContent text={text} formula />)
    expect(container.querySelector('.math-content-host')?.textContent).toBe(text)
    expect(screen.getByText(/已保留原文/)).toBeInTheDocument()
  })

  it('does not retain global macros across cards or text updates', () => {
    const { container, rerender } = render(<MathContent text={String.raw`\gdef\foo{123}\foo`} formula />)
    expect(container.querySelector('.katex')).not.toBeNull()
    rerender(<MathContent text={String.raw`\foo`} formula />)
    expect(container.querySelector('.katex')).toBeNull()
    expect(container.querySelector('.math-content-host')?.textContent).toBe(String.raw`\foo`)
    rerender(<MathContent text="x=3" formula />)
    expect(container.querySelector('.katex')).not.toBeNull()
    expect(screen.queryByText(/已保留原文/)).not.toBeInTheDocument()
  })

  it('keeps oversized input verbatim instead of attempting expensive rendering', () => {
    const text = 'x'.repeat(16_385)
    const { container } = render(<MathContent text={text} formula />)
    expect(container.querySelector('.math-content-host')?.textContent).toBe(text)
    expect(container.querySelector('.katex')).toBeNull()
  })

  it('handles React StrictMode and repeated input changes without duplicate output', () => {
    const { container, rerender } = render(<StrictMode><MathContent text={String.raw`\(x=1\)`} /></StrictMode>)
    expect(container.querySelectorAll('.katex')).toHaveLength(1)
    rerender(<StrictMode><MathContent text={String.raw`\(y=2\)`} /></StrictMode>)
    expect(container.querySelectorAll('.katex')).toHaveLength(1)
    expect(container.querySelector('annotation')?.textContent).toBe('y=2')
    rerender(<StrictMode><MathContent text="plain content" /></StrictMode>)
    expect(container.querySelectorAll('.katex')).toHaveLength(0)
    expect(container.querySelector('.math-content-host')?.textContent).toBe('plain content')
  })
})
