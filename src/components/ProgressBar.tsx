'use client'

interface ProgressBarProps {
  progress: number
  status: 'pending' | 'processing' | 'completed' | 'error'
}

const statusMessages = {
  pending: 'Preparing your video...',
  processing: 'AI is generating captions...',
  completed: 'Video ready for download!',
  error: 'Something went wrong'
}

export default function ProgressBar({ progress, status }: ProgressBarProps) {
  const getStatusColor = () => {
    switch (status) {
      case 'completed': return 'bg-gradient-to-r from-green-500 to-emerald-500'
      case 'error': return 'bg-gradient-to-r from-red-500 to-red-600'
      case 'processing': return 'bg-gradient-to-r from-purple-500 to-blue-500'
      default: return 'bg-gradient-to-r from-gray-500 to-gray-600'
    }
  }

  const getBackgroundColor = () => {
    switch (status) {
      case 'completed': return 'bg-green-500/20'
      case 'error': return 'bg-red-500/20'
      case 'processing': return 'bg-purple-500/20'
      default: return 'bg-gray-500/20'
    }
  }

  return (
    <div className="w-full space-y-6">
      <div className="flex items-center justify-between">
        <span className="text-lg font-semibold text-white">
          {statusMessages[status]}
        </span>
        <span className="text-2xl font-bold text-white bg-white/10 px-3 py-1 rounded-full">
          {progress}%
        </span>
      </div>
      
      <div className={`w-full rounded-full h-4 ${getBackgroundColor()} backdrop-blur-sm border border-white/10`}>
        <div
          className={`h-4 rounded-full transition-all duration-500 ease-out ${getStatusColor()} shadow-lg relative overflow-hidden`}
          style={{ width: `${progress}%` }}
        >
          {status === 'processing' && (
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse"></div>
          )}
        </div>
      </div>
      
      {status === 'processing' && (
        <div className="text-center">
          <div className="inline-flex items-center space-x-3 text-gray-300">
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse"></div>
              <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" style={{animationDelay: '0.1s'}}></div>
              <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
            </div>
            <span className="text-sm">
              This usually takes 30-60 seconds
            </span>
          </div>
        </div>
      )}
    </div>
  )
}