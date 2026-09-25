import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { RecordingPage } from './RecordingPage'

describe('RecordingPage', () => {
  it('explains when the browser cannot record audio', () => {
    render(<RecordingPage />)

    expect(screen.getByRole('heading', { name: '课堂录音' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '开始录音' }))
    expect(screen.getByRole('alert')).toHaveTextContent('不支持录音')
  })
})
