import { render, screen, waitFor } from '@testing-library/react'
import { vi, describe, it, expect } from 'vitest'

// Mock react-router hooks to provide a URL query and capture navigation
const navigateMock = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom') as any
  return {
    ...actual,
    useLocation: () => ({ search: '?url=https://example.com' }),
    useNavigate: () => navigateMock,
  }
})

// Mock PipelineService to simulate pipeline progress and completion
const mockRunFull = vi.fn()
vi.mock('../../../services/PipelineService', () => ({
  PipelineService: class {
    runFullPipeline(url: string, perStepProgress: any, _a: any, _b: any, _c: any) {
      // record call so the mock and url param are used (avoids unused-variable errors)
      mockRunFull(url)
      // simulate per-step events synchronous
      if (perStepProgress) {
        perStepProgress('initializing', { step: 'initializing', status: 'start' })
        perStepProgress('crawling', { step: 'crawling', status: 'start' })
        perStepProgress('pipeline', { step: 'pipeline', status: 'done' })
      }
      return Promise.resolve({})
    }
    closeAll() {}
  }
}))

// Mock ChatInterface so we can assert it appears after pipeline done
vi.mock('../../chatcomponents/ChatInterface', () => ({
  default: (props: any) => <div data-testid="chat-interface" data-url={props.url} />,
}))

import CustomChat from './CustomChat'

describe('CustomChat', () => {
  it('runs pipeline and shows ChatInterface after done', async () => {
    render(<CustomChat />)

    // while pipeline not done, PipelineProgess would be mounted. After mocked completion,
    // ChatInterface should appear
    await waitFor(() => {
      expect(screen.getByTestId('chat-interface')).toBeTruthy()
    })
  })
})
