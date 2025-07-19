'use client'

import { useState, useEffect } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import ProgressBar from '@/components/ProgressBar'

interface JobStatus {
  progress: number
  status: 'pending' | 'processing' | 'completed' | 'error'
  error?: string
  downloadUrl?: string
}

export default function StatusPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const jobId = searchParams.get('jobId')
  const [jobStatus, setJobStatus] = useState<JobStatus>({
    progress: 0,
    status: 'pending'
  })
  const [timeElapsed, setTimeElapsed] = useState(0)

  useEffect(() => {
    if (!jobId) return

    const pollStatus = async () => {
      try {
        const response = await fetch(`/api/status/${jobId}`)
        if (response.ok) {
          const status = await response.json()
          setJobStatus(status)
        }
      } catch (error) {
        console.error('Status poll error:', error)
      }
    }

    pollStatus()
    const interval = setInterval(pollStatus, 2000)

    return () => clearInterval(interval)
  }, [jobId])

  useEffect(() => {
    const timer = setInterval(() => {
      setTimeElapsed(prev => prev + 1)
    }, 1000)

    return () => clearInterval(timer)
  }, [])

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  if (!jobId) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
        <div className="text-center">
          <div className="w-16 h-16 bg-red-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <div className="text-red-400 text-lg font-medium">Invalid job ID</div>
          <button
            onClick={() => router.push('/')}
            className="mt-4 text-purple-400 hover:text-purple-300 underline"
          >
            Go back to upload
          </button>
        </div>
      </div>
    )
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <div className="container mx-auto px-4 pt-8 pb-4">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-purple-600 to-blue-600 rounded-2xl mb-6 shadow-lg">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent mb-2">
            Processing Your Video
          </h1>
          <p className="text-gray-400">AI is working its magic on your content</p>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 pb-8">
        <div className="max-w-2xl mx-auto">
          <div className="bg-white/10 backdrop-blur-lg rounded-3xl border border-white/20 shadow-2xl p-8 md:p-12">
            
            {/* Job Info */}
            <div className="text-center mb-8">
              <div className="text-gray-400 text-sm mb-2">Job ID: {jobId}</div>
              <div className="text-gray-400 text-sm">Time elapsed: {formatTime(timeElapsed)}</div>
            </div>

            <ProgressBar progress={jobStatus.progress} status={jobStatus.status} />
            
            {/* Status Messages */}
            {jobStatus.status === 'pending' && (
              <div className="mt-8 p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-blue-500/20 rounded-xl flex items-center justify-center">
                    <svg className="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <div className="text-blue-300 font-medium">Initializing</div>
                    <div className="text-blue-200/70 text-sm">Setting up your video processing pipeline...</div>
                  </div>
                </div>
              </div>
            )}

            {jobStatus.status === 'processing' && (
              <div className="mt-8 space-y-4">
                <div className="p-4 bg-purple-500/10 border border-purple-500/20 rounded-xl">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-purple-500/20 rounded-xl flex items-center justify-center">
                      <svg className="w-4 h-4 text-purple-400 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    </div>
                    <div>
                      <div className="text-purple-300 font-medium">AI Processing</div>
                      <div className="text-purple-200/70 text-sm">Transcribing audio and generating styled captions...</div>
                    </div>
                  </div>
                </div>

                {/* Processing Steps */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                  <div className={`p-3 rounded-xl ${jobStatus.progress > 20 ? 'bg-green-500/10 border border-green-500/20' : 'bg-gray-500/10 border border-gray-500/20'}`}>
                    <div className={`w-8 h-8 mx-auto mb-2 rounded-full flex items-center justify-center ${jobStatus.progress > 20 ? 'bg-green-500' : 'bg-gray-500'}`}>
                      <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a2 2 0 012-2h2a2 2 0 012 2v6a3 3 0 01-3 3z" />
                      </svg>
                    </div>
                    <div className={`text-sm font-medium ${jobStatus.progress > 20 ? 'text-green-400' : 'text-gray-400'}`}>
                      Audio Analysis
                    </div>
                  </div>
                  
                  <div className={`p-3 rounded-xl ${jobStatus.progress > 60 ? 'bg-green-500/10 border border-green-500/20' : 'bg-gray-500/10 border border-gray-500/20'}`}>
                    <div className={`w-8 h-8 mx-auto mb-2 rounded-full flex items-center justify-center ${jobStatus.progress > 60 ? 'bg-green-500' : 'bg-gray-500'}`}>
                      <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zM21 5a2 2 0 00-2-2h-4a2 2 0 00-2 2v12a4 4 0 004 4h4a2 2 0 002-2V5z" />
                      </svg>
                    </div>
                    <div className={`text-sm font-medium ${jobStatus.progress > 60 ? 'text-green-400' : 'text-gray-400'}`}>
                      Style Applied
                    </div>
                  </div>
                  
                  <div className={`p-3 rounded-xl ${jobStatus.progress > 90 ? 'bg-green-500/10 border border-green-500/20' : 'bg-gray-500/10 border border-gray-500/20'}`}>
                    <div className={`w-8 h-8 mx-auto mb-2 rounded-full flex items-center justify-center ${jobStatus.progress > 90 ? 'bg-green-500' : 'bg-gray-500'}`}>
                      <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <div className={`text-sm font-medium ${jobStatus.progress > 90 ? 'text-green-400' : 'text-gray-400'}`}>
                      Video Render
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            {jobStatus.status === 'error' && (
              <div className="mt-8 p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-red-500/20 rounded-xl flex items-center justify-center">
                    <svg className="w-4 h-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                  </div>
                  <div>
                    <div className="text-red-300 font-medium">Processing Failed</div>
                    <div className="text-red-200/70 text-sm">{jobStatus.error}</div>
                  </div>
                </div>
                <button
                  onClick={() => router.push('/')}
                  className="mt-4 w-full bg-red-500/20 hover:bg-red-500/30 text-red-300 font-medium py-2 px-4 rounded-lg transition-colors"
                >
                  Try Again
                </button>
              </div>
            )}
            
            {jobStatus.status === 'completed' && jobStatus.downloadUrl && (
              <div className="mt-8 space-y-4">
                <div className="p-6 bg-green-500/10 border border-green-500/20 rounded-xl text-center">
                  <div className="w-16 h-16 bg-green-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <h3 className="text-green-300 font-bold text-xl mb-2">Video Ready!</h3>
                  <p className="text-green-200/70 text-sm mb-6">Your captioned video has been processed successfully</p>
                  
                  <div className="space-y-3">
                    <a
                      href={`/api/output/${jobStatus.downloadUrl?.split('/').pop()}`}
                      download
                      className="block w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-bold py-4 px-6 rounded-xl transition-all duration-300 transform hover:scale-105 shadow-lg"
                    >
                      <div className="flex items-center justify-center space-x-3">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <span>Download Your Video</span>
                      </div>
                    </a>
                    
                    <button
                      onClick={() => router.push('/')}
                      className="w-full bg-white/10 hover:bg-white/20 text-white font-medium py-3 px-6 rounded-xl transition-colors border border-white/20"
                    >
                      Create Another Video
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  )
}