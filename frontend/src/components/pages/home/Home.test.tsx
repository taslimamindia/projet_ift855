import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect, beforeEach } from 'vitest'
const navigateMock = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...(actual as any),
    useNavigate: () => navigateMock,
  }
})

import Home from './Home'

describe('Home component', () => {
  beforeEach(() => {
    navigateMock.mockReset()
  })

  it('navigates to gov chat when clicking the gov button', async () => {
    render(<Home />)
    const btn = screen.getByRole('button', { name: /Démarrer le Chat/i })
    await userEvent.click(btn)
    expect(navigateMock).toHaveBeenCalledWith('/chat/gov/gn')
  })

  it('submits custom url and navigates to custom chat with encoded url', async () => {
    render(<Home />)
    const input = screen.getByPlaceholderText('https://') as HTMLInputElement
  fireEvent.change(input, { target: { value: 'https://example.com' } })
    expect(input.value).toContain('https://example.com')

    const submitBtn = screen.getByRole('button', { name: /Lancer le Chat/i })
    await userEvent.click(submitBtn)

    expect(navigateMock).toHaveBeenCalledWith('/chat/custom?url=' + encodeURIComponent('https://example.com') + '&max_depth=250')
  })
})
