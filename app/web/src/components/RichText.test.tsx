import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { FormulaBlock, RichText, normalizeMathDelimiters, normalizeFormula } from './RichText'

describe('RichText', () => {
  it('preserves parenthesized exponents in legacy formulas', () => {
    expect(normalizeFormula('a^(1/(p+1)) + x_(n+1)')).toBe('a^{1/(p+1)} + x_{n+1}')
    expect(normalizeFormula('x^(p')).toBe('x^(p')
    expect(normalizeFormula('\\frac{x}{y}^(2)')).toBe('\\frac{x}{y}^(2)')
  })
  it('renders Chinese prose, inline math, display fractions and accessible MathML', () => {
    const { container } = render(<RichText content={'设 \\(f\\) 可测。\\[\\frac{1}{p}+\\frac{1}{q}=1\\]'} />)
    expect(container.textContent).toContain('可测')
    expect(container.querySelectorAll('.katex').length).toBe(2)
    expect(container.querySelector('.katex-display')).toBeTruthy()
    expect(container.querySelector('math')).toBeTruthy()
    expect(container.querySelector('.katex-error')).toBeNull()
  })
  it('keeps code examples literal', () => {
    const code = '`\\(x\\)`\n\n```tex\n\\[x\\]\n```'
    expect(normalizeMathDelimiters(code)).toBe(code)
  })
  it.each(['x^2', '$x^2$', '$$x^2$$', '\\(x^2\\)', '\\[x^2\\]'])('accepts formula delimiters: %s', formula => {
    const { container } = render(<FormulaBlock formula={formula} />)
    expect(container.querySelector('.katex-display')).toBeTruthy()
    expect(screen.getByRole('math')).toHaveAccessibleName(formula)
  })
  it('preserves unsupported formulas as visible source', () => {
    render(<FormulaBlock formula={'\\notACommand{x}'} />)
    expect(screen.getByText('\\notACommand{x}')).toBeVisible()
    expect(screen.getByText('该公式语法暂不支持，已保留原文。')).toBeVisible()
  })
  it('does not turn markup into executable HTML or remote image requests', () => {
    const { container } = render(<RichText content={'<script>alert(1)</script>\n![test](https://example.com/private.png)\n[x](javascript:alert(1))'} />)
    expect(container.querySelector('script, img, iframe')).toBeNull()
    expect(container.querySelector('a')?.getAttribute('href')).not.toMatch(/^javascript:/)
  })
})
