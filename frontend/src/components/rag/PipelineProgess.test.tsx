import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'

import PipelineProgess from './PipelineProgess'

describe('PipelineProgess', () => {
  it('shows failure alert when status is failed', () => {
    render(<PipelineProgess currentStep="initializing" status="failed" />)
    expect(screen.getByText(/Le pipeline a échoué/i)).toBeTruthy()
  })

  it('renders an image and label for a known currentStep', () => {
    render(<PipelineProgess currentStep="crawling" status="start" />)
    expect(screen.getByAltText(/Exploration du site/i)).toBeTruthy()
    expect(screen.getByText(/Exploration du site.*en cours/i)).toBeTruthy()
  })
})
