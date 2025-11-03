import { render, screen } from '@testing-library/react'
import { vi, describe, it, expect } from 'vitest'

// Mock ChatInterface to avoid network/service calls
vi.mock('../../chatcomponents/ChatInterface', () => ({
  default: (props: any) => <div data-testid="chat-interface" data-url={props.url} />,
}))

import GovGnChat from './GovGnChat'

describe('GovGnChat', () => {
  it('renders heading and chat interface', () => {
    render(<GovGnChat />)
    expect(screen.getByText(/Chat sur les données du Gouvernement Guinéen/i)).toBeTruthy()
    expect(screen.getByTestId('chat-interface')).toBeTruthy()
  })
})
