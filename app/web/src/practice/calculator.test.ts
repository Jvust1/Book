import { describe, expect, it } from 'vitest'
import { calculateExpression } from './calculator'

describe('real math.js bounded practice calculator', () => {
  it.each([
    ['1 + 2 * 3', '7'], ['sin(pi/2)', '1'], ['0.1 + 0.2', '0.3'],
    ['det([[1,2],[3,4]])', '-2'], ['inv([[4,7],[2,6]])', '[[0.6, -0.7], [-0.2, 0.4]]'],
    ['transpose([[1,2],[3,4]])', '[[1, 3], [2, 4]]'], ['dot([1,2],[3,4])', '11'],
    ['sqrt(-1)', 'i'], ['(1+0.05)^30', '4.3219423751507'],
    ['2^(-2)', '0.25'], ['2^(2)', '4'], ['2^((-2))', '0.25'],
  ])('evaluates %s with the pinned upstream implementation', (expression, formatted) => {
    expect(calculateExpression(expression)).toMatchObject({ status: 'ok', engine: 'mathjs@15.2.0', expression, formatted })
  })

  it.each([
    'import("x")', 'createUnit("custom")', 'evaluate("1+1")', 'parse("1+1")',
    'simplify("x+x")', 'derivative("x^2", "x")', 'resolve("x")', 'reviver({})',
    'x = 1', 'f(x) = x', 'a.b', 'a[1]', '{x:1}', '[1:1000000]', 'range(1000000)',
    'zeros(1000000)', 'ones(1000000)', 'random()', '1; 2', 'true', 'null',
    '"text"', 'constructor()', 'factorial(1000000)', '1000000!', 'Infinity', 'NaN',
    '2^129', '2^(-129)', '2^((129))', '2^(64+64)', '[[[1]]]', '[1,2,3,4,5,6,7,8,9]',
  ])('rejects unsupported capability %s', expression => {
    expect(calculateExpression(expression).status).toBe('error')
  })

  it('handles zero division, singular inverse and invalid syntax without a result', () => {
    expect(calculateExpression('1/0')).toEqual({ status: 'error', code: 'non_finite_result' })
    expect(calculateExpression('inv([[1,2],[2,4]])').status).toBe('error')
    expect(calculateExpression('sin(').status).toBe('error')
    expect(calculateExpression('x'.repeat(2049)).status).toBe('error')
    expect(calculateExpression('sqrt(4)')).toMatchObject({ status: 'ok', formatted: '2' })
  })

  it('accepts bounded arrays and rejects overly large ASTs before evaluating', () => {
    const matrix = '[' + Array.from({ length: 8 }, (_, r) => '[' + Array.from({ length: 8 }, (_, c) => r === c ? '1' : '0').join(',') + ']').join(',') + ']'
    expect(calculateExpression(`det(${matrix})`)).toMatchObject({ status: 'ok', formatted: '1' })
    expect(calculateExpression(Array(100).fill('1').join('+')).status).toBe('error')
    expect(calculateExpression('2^' + '('.repeat(25) + '1' + ')'.repeat(25)).status).toBe('error')
  })
})
