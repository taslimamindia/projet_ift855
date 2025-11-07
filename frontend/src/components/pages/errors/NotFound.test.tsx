/// <reference types="jest" />
import '@testing-library/jest-dom'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import NotFound from './NotFound'

describe('NotFound page', () => {
  it('renders 404 message and link to home', () => {
    render(
      <MemoryRouter>
        <NotFound />
      </MemoryRouter>
    )
    expect(screen.getByText(/404 - Page introuvable/i)).toBeTruthy()
    const link = screen.getByRole('link', { name: /Retour à l'accueil/i })
    expect(link).toHaveAttribute('href', '/')
  })
})
