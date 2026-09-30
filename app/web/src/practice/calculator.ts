import { all, create, type ArrayNode, type ConstantNode, type FunctionNode, type MathNode, type OperatorNode, type ParenthesisNode, type SymbolNode } from 'mathjs'

export const CALCULATOR_ENGINE = 'mathjs@15.2.0'
export const MAX_EXPRESSION_LENGTH = 2048
const functions = new Set(['sqrt', 'abs', 'sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'exp', 'log', 'round', 'floor', 'ceil', 'min', 'max', 'sum', 'mean', 'det', 'inv', 'transpose', 'trace', 'norm', 'dot', 'cross'])
const constants = new Set(['pi', 'e', 'i'])
const operators = new Set(['+', '-', '*', '/', '^'])
const math = create(all, { matrix: 'Array', number: 'number' })
const parse = math.parse
// Defense in depth, following the upstream security guidance. None are in the grammar.
const disabled = () => { throw new Error('disabled capability') }
math.import({ import: disabled, createUnit: disabled, reviver: disabled, evaluate: disabled,
  parse: disabled, simplify: disabled, derivative: disabled, resolve: disabled }, { override: true })

export type CalculationOutcome =
  | { status: 'ok'; engine: typeof CALCULATOR_ENGINE; expression: string; formatted: string; kind: 'number' | 'complex' | 'array' }
  | { status: 'error'; code: 'invalid_expression' | 'unsupported_expression' | 'non_finite_result' | 'unavailable' | 'timeout' | 'cancelled' }

function literalNumber(node: MathNode): number | null {
  if (node.type === 'ConstantNode' && typeof (node as ConstantNode).value === 'number') return (node as ConstantNode).value as number
  if (node.type === 'OperatorNode') {
    const value = node as OperatorNode
    if (value.args.length === 1 && (value.op === '-' || value.op === '+')) {
      const inner = literalNumber(value.args[0])
      return inner === null ? null : value.op === '-' ? -inner : inner
    }
  }
  return null
}

function validate(root: MathNode): void {
  let count = 0
  function visit(node: MathNode, depth = 0, arrayDepth = 0): void {
    if (++count > 128 || depth > 20) throw new Error('expression budget')
    switch (node.type) {
      case 'ConstantNode': {
        const value = (node as ConstantNode).value
        if (typeof value !== 'number' || !Number.isFinite(value)) throw new Error('number only')
        return
      }
      case 'SymbolNode':
        if (!constants.has((node as SymbolNode).name)) throw new Error('unknown constant')
        return
      case 'ParenthesisNode': visit((node as ParenthesisNode).content, depth + 1, arrayDepth); return
      case 'OperatorNode': {
        const value = node as OperatorNode
        if (!operators.has(value.op) || value.args.length < 1 || value.args.length > 2) throw new Error('unsupported operator')
        if (value.op === '^') {
          const exponent = value.args[1] && literalNumber(value.args[1])
          if (exponent === null || exponent === undefined || Math.abs(exponent) > 128) throw new Error('power budget')
        }
        value.args.forEach(arg => visit(arg, depth + 1, arrayDepth)); return
      }
      case 'FunctionNode': {
        const value = node as FunctionNode
        if (value.fn.type !== 'SymbolNode' || !functions.has(value.fn.name) || value.args.length < 1 || value.args.length > 8) throw new Error('unsupported function')
        value.args.forEach(arg => visit(arg, depth + 1, arrayDepth)); return
      }
      case 'ArrayNode': {
        const value = node as ArrayNode
        if (arrayDepth >= 2 || value.items.length < 1 || value.items.length > 8) throw new Error('array budget')
        value.items.forEach(item => visit(item, depth + 1, arrayDepth + 1)); return
      }
      default: throw new Error('unsupported syntax')
    }
  }
  visit(root)
}

function finiteResult(value: unknown, depth = 0): boolean {
  if (typeof value === 'number') return Number.isFinite(value)
  if (math.isComplex(value)) return Number.isFinite(value.re) && Number.isFinite(value.im)
  if (Array.isArray(value)) return depth < 2 && value.length > 0 && value.length <= 8 && value.every(item => finiteResult(item, depth + 1))
  return false
}

/** Run only from the worker in production; this export also supports real-engine tests. */
export function calculateExpression(expression: string): CalculationOutcome {
  if (typeof expression !== 'string' || !expression.trim() || expression.length > MAX_EXPRESSION_LENGTH || math.version !== '15.2.0') {
    return { status: 'error', code: 'invalid_expression' }
  }
  let node: MathNode
  try { node = parse(expression) } catch { return { status: 'error', code: 'invalid_expression' } }
  try { validate(node) } catch { return { status: 'error', code: 'unsupported_expression' } }
  try {
    const value: unknown = node.compile().evaluate(new Map())
    if (!finiteResult(value)) return { status: 'error', code: 'non_finite_result' }
    const formatted = math.format(value, { precision: 14 })
    if (formatted.length > 4096) return { status: 'error', code: 'unsupported_expression' }
    return { status: 'ok', engine: CALCULATOR_ENGINE, expression,
      formatted, kind: Array.isArray(value) ? 'array' : math.isComplex(value) ? 'complex' : 'number' }
  } catch { return { status: 'error', code: 'invalid_expression' } }
}
