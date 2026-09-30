import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { startCalculation } from '../practice/workerClient'
import type { CalculationOutcome } from '../practice/calculator'
import { PracticeScratchpad } from './PracticeScratchpad'

vi.mock('../practice/workerClient', () => ({ startCalculation: vi.fn() }))
afterEach(() => vi.clearAllMocks())
function deferred() {
  let resolve!: (value: CalculationOutcome) => void
  const result = new Promise<CalculationOutcome>(done => { resolve = done })
  const cancel = vi.fn(() => resolve({ status: 'error', code: 'cancelled' }))
  return { result, cancel, resolve }
}

describe('PracticeScratchpad lifecycle', () => {
  it('calculates only after explicit submit and prevents duplicate submissions', async () => {
    const user = userEvent.setup(); const task = deferred()
    vi.mocked(startCalculation).mockReturnValue(task)
    render(<PracticeScratchpad />)
    expect(startCalculation).not.toHaveBeenCalled()
    await user.click(screen.getByRole('button', { name: '行列式示例' }))
    expect(startCalculation).not.toHaveBeenCalled()
    const form = screen.getByRole('textbox', { name: '算式' }).closest('form')!
    fireEvent.submit(form); fireEvent.submit(form)
    expect(startCalculation).toHaveBeenCalledOnce()
    expect(startCalculation).toHaveBeenCalledWith('det([[1,2],[3,4]])')
    task.resolve({ status: 'ok', engine: 'mathjs@15.2.0', expression: 'det([[1,2],[3,4]])', formatted: '-2', kind: 'number' })
    expect(await screen.findByLabelText('演算结果')).toHaveTextContent('-2')
    expect(screen.getByRole('textbox', { name: '算式' })).toBeEnabled()
  })

  it('cancel keeps the input and lets the user retry', async () => {
    const user = userEvent.setup(); const task = deferred()
    vi.mocked(startCalculation).mockReturnValue(task)
    render(<PracticeScratchpad />)
    await user.type(screen.getByRole('textbox', { name: '算式' }), '1+1')
    await user.click(screen.getByRole('button', { name: /^计算$/ }))
    await user.click(screen.getByRole('button', { name: '取消计算' }))
    expect(await screen.findByText('已取消，输入仍保留')).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: '算式' })).toHaveValue('1+1')
    expect(screen.getByRole('button', { name: /^计算$/ })).toBeEnabled()
    expect(task.cancel).toHaveBeenCalledOnce()
  })

  it('clear ignores a late result from a stopped worker', async () => {
    const user = userEvent.setup(); const task = deferred(); task.cancel.mockImplementation(() => {})
    vi.mocked(startCalculation).mockReturnValue(task)
    render(<PracticeScratchpad />)
    await user.type(screen.getByRole('textbox', { name: '算式' }), '1')
    await user.click(screen.getByRole('button', { name: /^计算$/ }))
    await user.click(screen.getByRole('button', { name: '清空演算区' }))
    task.resolve({ status: 'ok', engine: 'mathjs@15.2.0', expression: '1', formatted: '1', kind: 'number' })
    await waitFor(() => expect(task.cancel).toHaveBeenCalledOnce())
    expect(screen.queryByLabelText('演算结果')).not.toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: '算式' })).toHaveValue('')
  })

  it('unmount stops active work and later calculations do not restore old data', async () => {
    const user = userEvent.setup(); const task = deferred()
    vi.mocked(startCalculation).mockReturnValue(task)
    const view = render(<PracticeScratchpad />)
    await user.click(screen.getByRole('button', { name: '三角函数示例' }))
    await user.click(screen.getByRole('button', { name: /^计算$/ }))
    view.unmount()
    expect(task.cancel).toHaveBeenCalledOnce()
    render(<PracticeScratchpad />)
    expect(screen.getByRole('textbox', { name: '算式' })).toHaveValue('')
    expect(screen.queryByLabelText('演算结果')).not.toBeInTheDocument()
  })
})
