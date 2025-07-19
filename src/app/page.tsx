'use client'

import { useState } from 'react'
import DragDrop from '@/components/DragDrop'
import PresetSelector from '@/components/PresetSelector'
import { useRouter } from 'next/navigation'

export default function Home() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [selectedPreset, setSelectedPreset] = useState<string>('highlight-bold')
  const [fontSize, setFontSize] = useState<number>(42) // Default font size
  const [captionMode, setCaptionMode] = useState<'sentences' | 'words'>('sentences')
  const [showFiller, setShowFiller] = useState<boolean>(false) // Default to clean mode
  const [isUploading, setIsUploading] = useState(false)
  const router = useRouter()

  const handleUpload = async () => {
    if (!selectedFile) return

    setIsUploading(true)
    const formData = new FormData()
    formData.append('video', selectedFile)
    formData.append('preset', selectedPreset)
    formData.append('fontSize', fontSize.toString())
    formData.append('captionMode', captionMode)
    formData.append('showFiller', showFiller.toString())

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) throw new Error('Upload failed')

      const { jobId } = await response.json()
      router.push(`/status?jobId=${jobId}`)
    } catch (error) {
      console.error('Upload error:', error)
      alert('Upload failed. Please try again.')
    } finally {
      setIsUploading(false)
    }
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
          <h1 className="text-5xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent mb-4">
            CapFuse AI
          </h1>
          <p className="text-xl text-gray-300 mb-8 max-w-2xl mx-auto">
            Transform your videos with AI-powered captions in seconds. Choose from trendy styles that make your content pop.
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 pb-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white/10 backdrop-blur-lg rounded-3xl border border-white/20 shadow-2xl p-8 md:p-12">
            
            {/* Progress Steps */}
            <div className="flex items-center justify-center mb-12">
              <div className="flex items-center space-x-4">
                <div className={`flex items-center justify-center w-10 h-10 rounded-full text-sm font-medium ${
                  selectedFile ? 'bg-green-500 text-white' : 'bg-purple-600 text-white'
                }`}>
                  1
                </div>
                <div className="text-white text-sm font-medium">Upload</div>
                <div className={`w-12 h-0.5 ${selectedFile ? 'bg-green-500' : 'bg-gray-600'}`}></div>
                <div className={`flex items-center justify-center w-10 h-10 rounded-full text-sm font-medium ${
                  selectedFile ? 'bg-purple-600 text-white' : 'bg-gray-600 text-gray-400'
                }`}>
                  2
                </div>
                <div className="text-white text-sm font-medium">Style</div>
                <div className="w-12 h-0.5 bg-gray-600"></div>
                <div className="flex items-center justify-center w-10 h-10 rounded-full text-sm font-medium bg-gray-600 text-gray-400">
                  3
                </div>
                <div className="text-white text-sm font-medium">Generate</div>
              </div>
            </div>

            <div className="space-y-8">
              <DragDrop onFileSelect={setSelectedFile} selectedFile={selectedFile} />
              
              <PresetSelector
                selectedPreset={selectedPreset}
                onPresetChange={setSelectedPreset}
                fontSize={fontSize}
                onFontSizeChange={setFontSize}
                captionMode={captionMode}
                onCaptionModeChange={setCaptionMode}
                showFiller={showFiller}
                onShowFillerChange={setShowFiller}
              />
              
              <div className="flex flex-col items-center space-y-4">
                <button
                  onClick={handleUpload}
                  disabled={!selectedFile || isUploading}
                  className="group relative w-full max-w-md bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-500 disabled:to-gray-600 text-white font-bold py-4 px-8 rounded-2xl transition-all duration-300 transform hover:scale-105 disabled:hover:scale-100 shadow-lg hover:shadow-xl disabled:shadow-none"
                >
                  <div className="flex items-center justify-center space-x-3">
                    {isUploading ? (
                      <>
                        <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <span>Processing...</span>
                      </>
                    ) : (
                      <>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        <span>Generate Captions</span>
                      </>
                    )}
                  </div>
                </button>
                
                {!selectedFile && (
                  <p className="text-gray-400 text-sm text-center">
                    Upload a video to get started
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Features Section */}
          <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10 p-6 text-center">
              <div className="w-12 h-12 bg-green-500/20 rounded-xl flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-white font-semibold mb-2">Lightning Fast</h3>
              <p className="text-gray-400 text-sm">AI-powered processing in under 60 seconds</p>
            </div>
            
            <div className="bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10 p-6 text-center">
              <div className="w-12 h-12 bg-purple-500/20 rounded-xl flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zM21 5a2 2 0 00-2-2h-4a2 2 0 00-2 2v12a4 4 0 004 4h4a2 2 0 002-2V5z" />
                </svg>
              </div>
              <h3 className="text-white font-semibold mb-2">Trendy Styles</h3>
              <p className="text-gray-400 text-sm">Modern caption styles that grab attention</p>
            </div>
            
            <div className="bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10 p-6 text-center">
              <div className="w-12 h-12 bg-blue-500/20 rounded-xl flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-white font-semibold mb-2">High Quality</h3>
              <p className="text-gray-400 text-sm">Professional results ready for social media</p>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}