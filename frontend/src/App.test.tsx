import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'

// Mock pages to keep tests focused and fast
vi.mock('./components/pages/home/Home', () => ({ default: () => <div>HomeStub</div> }))
vi.mock('./components/pages/chatpage/GovGnChat', () => ({ default: () => <div>GovGnStub</div> }))
vi.mock('./components/pages/chatpage/CustomChat', () => ({ default: () => <div>CustomChatStub</div> }))
vi.mock('./components/pages/errors/NotFound', () => ({ default: () => <div>NotFoundStub</div> }))

import App from './App'

describe('App routes', () => {
  it('renders home at root', () => {
    render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>)
    expect(screen.getByText(/HomeStub/i)).toBeTruthy()
  })

  it('renders gov chat route', () => {
    render(<MemoryRouter initialEntries={["/chat/gov/gn"]}><App /></MemoryRouter>)
    expect(screen.getByText(/GovGnStub/i)).toBeTruthy()
  })

  it('renders not found for unknown route', () => {
    render(<MemoryRouter initialEntries={["/nope"]}><App /></MemoryRouter>)
    expect(screen.getByText(/NotFoundStub/i)).toBeTruthy()
  })
})
