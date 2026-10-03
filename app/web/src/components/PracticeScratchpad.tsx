import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { startCalculation, type CalculationTask } from '../practice/workerClient'
import type { CalculationOutcome } from '../practice/calculator'

const ERROR_MESSAGES = {
  invalid_expression: '算式无法计算，请检查输入、矩阵维度或奇异矩阵',
  unsupported_expression: '超出支持范围，请使用数值、小矩阵和列出的函数',
  non_finite_result: '结果不是有限数值，请检查除零、溢出或定义域',
  unavailable: '本地计算工作进程暂不可用，可重试',
  timeout: '计算已超时并停止，可简化算式后重试',
  cancelled: '已取消，输入仍保留',
}

export function PracticeScratchpad() {
  const [expression, setExpression] = useState('')
  const [outcome, setOutcome] = useState<CalculationOutcome | null>(null)
  const [busy, setBusy] = useState(false)
  const active = useRef<CalculationTask | null>(null)

  useEffect(() => () => {
    const task = active.current
    active.current = null
    task?.cancel()
  }, [])

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (active.current) return
    const text = expression.trim()
    if (!text || text.length > 2048) { setOutcome({ status: 'error', code: 'invalid_expression' }); return }
    setOutcome(null)
    setBusy(true)
    const task = startCalculation(text)
    active.current = task
    void task.result.then(value => {
      if (active.current !== task) return
      active.current = null
      setBusy(false)
      setOutcome(value)
    })
  }
  const cancel = () => { active.current?.cancel() }
  const clear = () => {
    const task = active.current
    active.current = null
    task?.cancel()
    setBusy(false)
    setExpression('')
    setOutcome(null)
  }
  const example = (value: string) => { setExpression(value); setOutcome(null) }

  return (
    <section className="practice-scratchpad" aria-label="本地演算辅助">
      <h2>本地演算辅助</h2>
      <p>用于自行核对数值和小矩阵，采用双精度近似。结果不写入学习进度，也不作为教材标准答案或自动评分。</p>
      <p className="secondary-text">三角函数使用弧度；数组最多两层、每层 8 项；超过 5 秒自动停止。刷新或离开刷题页后清空。</p>
      <div className="scratchpad-examples">
        <button type="button" className="secondary-button" disabled={busy} onClick={() => example('sin(pi / 2)')}>三角函数示例</button>
        <button type="button" className="secondary-button" disabled={busy} onClick={() => example('det([[1,2],[3,4]])')}>行列式示例</button>
        <button type="button" className="secondary-button" disabled={busy} onClick={() => example('inv([[4,7],[2,6]])')}>逆矩阵示例</button>
      </div>
      <form onSubmit={submit} className="scratchpad-form">
        <label htmlFor="practice-expression">算式</label>
        <textarea id="practice-expression" rows={3} maxLength={2048} disabled={busy} value={expression}
          onChange={event => { setExpression(event.target.value); setOutcome(null) }} placeholder="例如：sqrt(2) 或 det([[1,2],[3,4]])" />
        <div className="scratchpad-actions">
          <button className="secondary-button" type="submit" disabled={busy || !expression.trim()}>{busy ? '正在计算…' : '计算'}</button>
          {busy ? <button className="secondary-button" type="button" onClick={cancel}>取消计算</button> : null}
          <button className="secondary-button" type="button" onClick={clear}>清空演算区</button>
        </div>
      </form>
      <div aria-live="polite">
        {outcome?.status === 'error' ? <p role="status">{ERROR_MESSAGES[outcome.code]}</p> : null}
        {outcome?.status === 'ok' ? <div className="scratchpad-result">
          <p>结果（近似） · {outcome.kind === 'array' ? '向量 / 矩阵' : outcome.kind === 'complex' ? '复数' : '数值'}</p>
          <pre aria-label="演算结果">{outcome.formatted}</pre>
          <p className="secondary-text">由 {outcome.engine} 在本机计算</p>
        </div> : null}
      </div>
      <details><summary>支持的函数</summary><p>sqrt、abs、sin、cos、tan、asin、acos、atan、exp、log、round、floor、ceil、min、max、sum、mean、det、inv、transpose、trace、norm、dot、cross。常数：pi、e、i。幂指数须为绝对值不超过 128 的字面数值。</p></details>
    </section>
  )
}
