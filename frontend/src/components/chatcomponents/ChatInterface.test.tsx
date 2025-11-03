import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect, beforeAll, beforeEach } from 'vitest'

// Mock the backend service used by ChatInterface
const mockSend = vi.fn()
vi.mock('../../services/ChatService', () => ({
  sendQueryToBackend: (...args: any[]) => mockSend(...args),
}))

import ChatInterface from './ChatInterface'

describe('ChatInterface', () => {
  beforeAll(() => {
    // jsdom doesn't implement scrollIntoView; mock to avoid errors during tests
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (Element.prototype as any).scrollIntoView = () => {}
  })

  beforeEach(() => {
    mockSend.mockReset()
  })

  it('renders suggestions and sends query when suggestion clicked', async () => {
    mockSend.mockResolvedValueOnce({ response: 'Réponse IA' })

    render(<ChatInterface url="https://example.com" suggestions={["Question 1"]} />)

    // suggestion button present
    const sugBtn = screen.getByRole('button', { name: /Question 1/i })
    await userEvent.click(sugBtn)

    // wait for AI response to appear
    await waitFor(() => {
      expect(mockSend).toHaveBeenCalled()
      expect(screen.getByText(/Réponse IA/i)).toBeTruthy()
    })
  })

  it('typing and pressing send triggers a query and clears input', async () => {
    mockSend.mockResolvedValueOnce({ response: 'OK' })

    render(<ChatInterface url="" suggestions={[]} />)

    const input = screen.getByPlaceholderText(/Posez votre question ici/i) as HTMLInputElement
    await userEvent.type(input, 'Bonjour')
    expect(input.value).toBe('Bonjour')

    const sendBtn = screen.getByRole('button', { name: /Envoyer/i })
    await userEvent.click(sendBtn)

    await waitFor(() => {
      expect(mockSend).toHaveBeenCalled()
      // input cleared
      expect(input.value).toBe('')
    })
  })
})
