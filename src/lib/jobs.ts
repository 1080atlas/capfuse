// Shared job storage
export interface Job {
  status: 'pending' | 'processing' | 'completed' | 'error'
  progress: number
  error?: string
  downloadUrl?: string
  createdAt: Date
}

// Use globalThis to persist across hot reloads in development
const globalForJobs = globalThis as unknown as {
  jobs: Map<string, Job> | undefined
}

export const jobs = globalForJobs.jobs ?? new Map<string, Job>()

if (process.env.NODE_ENV !== 'production') {
  globalForJobs.jobs = jobs
}