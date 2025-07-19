'use client'

import { useState, useCallback, useEffect } from 'react'

interface DragDropProps {
  onFileSelect: (file: File | null) => void
  selectedFile: File | null
}

export default function DragDrop({ onFileSelect, selectedFile }: DragDropProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const [showTooltip, setShowTooltip] = useState(false)

  // Prevent default browser drag and drop behavior
  useEffect(() => {
    const preventDefaults = (e: DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
    }

    document.addEventListener('dragenter', preventDefaults)
    document.addEventListener('dragover', preventDefaults)
    document.addEventListener('dragleave', preventDefaults)
    document.addEventListener('drop', preventDefaults)

    return () => {
      document.removeEventListener('dragenter', preventDefaults)
      document.removeEventListener('dragover', preventDefaults)
      document.removeEventListener('dragleave', preventDefaults)
      document.removeEventListener('drop', preventDefaults)
    }
  }, [])

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(true)
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    // Keep drag over state active
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    // Only set drag over to false if we're leaving the drop zone itself
    if (!e.currentTarget.contains(e.relatedTarget as Node)) {
      setIsDragOver(false)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)

    const files = Array.from(e.dataTransfer.files)
    const videoFile = files.find(file => 
      file.type.includes('video/') && 
      ['mp4', 'mov', 'webm'].some(ext => file.name.toLowerCase().endsWith(ext))
    )

    if (videoFile) {
      // Check file size (120MB limit)
      if (videoFile.size > 120 * 1024 * 1024) {
        alert('File too large. Maximum size is 120MB.')
        return
      }
      onFileSelect(videoFile)
    } else {
      alert('Please select a valid video file (MP4, MOV, or WEBM)')
    }
  }, [onFileSelect])

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      if (file.size > 120 * 1024 * 1024) {
        alert('File too large. Maximum size is 120MB.')
        return
      }
      onFileSelect(file)
    }
  }, [onFileSelect])

  const formatFileSize = (bytes: number) => {
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  const formatDuration = (file: File) => {
    // This would need to be implemented with actual video duration detection
    // For now, returning placeholder
    return "Duration check pending..."
  }

  return (
    <div className="w-full">
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white">Upload Your Video</h3>
          <div className="relative">
            <button
              onMouseEnter={() => setShowTooltip(true)}
              onMouseLeave={() => setShowTooltip(false)}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </button>
            {showTooltip && (
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg whitespace-nowrap tooltip z-10">
                Supported: MP4, MOV, WEBM • Max 120MB • Max 60s
                <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
              </div>
            )}
          </div>
        </div>
      </div>

      <div
        className={`relative border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-300 ${
          isDragOver
            ? 'border-purple-400 bg-purple-500/10 scale-105'
            : selectedFile
            ? 'border-green-400 bg-green-500/10'
            : 'border-gray-500 hover:border-gray-400 bg-white/5 hover:bg-white/10'
        }`}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {selectedFile ? (
          <div className="space-y-4">
            <div className="w-16 h-16 bg-green-500/20 rounded-2xl flex items-center justify-center mx-auto">
              <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <div className="text-green-400 font-semibold text-lg mb-2">File Ready!</div>
              <div className="text-white font-medium">{selectedFile.name}</div>
              <div className="text-gray-400 text-sm mt-2 space-y-1">
                <div>{formatFileSize(selectedFile.size)} • {selectedFile.type.split('/')[1].toUpperCase()}</div>
                <div className="flex items-center justify-center space-x-4 text-xs">
                  <span className="flex items-center space-x-1">
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>Duration detected on upload</span>
                  </span>
                  <span className="flex items-center space-x-1">
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                    </svg>
                    <span>Optimized for social</span>
                  </span>
                </div>
              </div>
            </div>
            <button
              onClick={() => onFileSelect(null)}
              className="text-red-400 hover:text-red-300 text-sm underline transition-colors"
            >
              Remove file
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="w-20 h-20 bg-gradient-to-r from-purple-600 to-blue-600 rounded-2xl flex items-center justify-center mx-auto shadow-lg">
              <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </div>
            
            <div>
              <p className="text-2xl font-bold text-white mb-2">
                {isDragOver ? 'Drop your video here' : 'Drag & drop your video'}
              </p>
              <p className="text-gray-400 mb-6">
                or click below to browse your files
              </p>
              
              <div className="flex flex-wrap items-center justify-center gap-6 text-sm text-gray-500 mb-6">
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 bg-green-400 rounded-full"></span>
                  <span>MP4, MOV, WEBM</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 bg-blue-400 rounded-full"></span>
                  <span>Max 120MB</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 bg-purple-400 rounded-full"></span>
                  <span>Max 60 seconds</span>
                </div>
              </div>
            </div>
            
            <input
              type="file"
              accept="video/mp4,video/quicktime,video/webm"
              onChange={handleFileInput}
              className="hidden"
              id="file-input"
            />
            <label
              htmlFor="file-input"
              className="inline-flex items-center space-x-3 bg-white/10 hover:bg-white/20 backdrop-blur-sm text-white font-medium py-3 px-6 rounded-xl cursor-pointer transition-all duration-300 border border-white/20 hover:border-white/30"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <span>Choose File</span>
            </label>
          </div>
        )}
        
        {isDragOver && (
          <div className="absolute inset-0 bg-purple-600/20 border-2 border-purple-400 border-dashed rounded-2xl flex items-center justify-center">
            <div className="text-purple-300 text-xl font-semibold">Drop to upload</div>
          </div>
        )}
      </div>
    </div>
  )
}