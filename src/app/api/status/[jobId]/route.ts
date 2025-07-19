import { NextRequest, NextResponse } from 'next/server'
import { jobs } from '@/lib/jobs'

export async function GET(
  request: NextRequest,
  { params }: { params: { jobId: string } }
) {
  try {
    const jobId = params.jobId

    if (!jobId) {
      return NextResponse.json({ error: 'Job ID required' }, { status: 400 })
    }

    console.log(`Looking for job ${jobId}. Total jobs: ${jobs.size}`)
    console.log(`Available jobs: ${Array.from(jobs.keys()).join(', ')}`)

    const job = jobs.get(jobId)
    
    if (!job) {
      return NextResponse.json({ error: 'Job not found' }, { status: 404 })
    }

    return NextResponse.json({
      status: job.status,
      progress: job.progress,
      error: job.error,
      downloadUrl: job.downloadUrl
    })
  } catch (error) {
    console.error('Status check error:', error)
    return NextResponse.json({ error: 'Status check failed' }, { status: 500 })
  }
}