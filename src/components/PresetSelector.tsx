'use client'

import { useState } from 'react'

interface PresetSelectorProps {
  selectedPreset: string
  onPresetChange: (preset: string) => void
  fontSize: number
  onFontSizeChange: (size: number) => void
  captionMode: 'sentences' | 'words'
  onCaptionModeChange: (mode: 'sentences' | 'words') => void
  showFiller: boolean
  onShowFillerChange: (show: boolean) => void
}

const presets = [
  {
    id: 'highlight-bold',
    name: 'Highlight Bold',
    description: 'Modern creator standard – bold white on TikTok-yellow bar',
    preview: 'Sample Text',
    category: 'TikTok Style',
    popularity: 95,
    backgroundColor: '#FFE600',
    textColor: '#FFFFFF',
    hasOutline: false,
    gradient: false
  },
  {
    id: 'neon-pop',
    name: 'Neon Pop',
    description: 'Gaming/meme hype – neon text with black outline for impact',
    preview: 'NEON TEXT',
    category: 'Gaming',
    popularity: 88,
    backgroundColor: 'transparent',
    textColor: '#2BFF88',
    hasOutline: true,
    gradient: false
  },
  {
    id: 'glass-glow',
    name: 'Glass Glow',
    description: 'Lifestyle/vlog chic – frosted glass with elegant styling',
    preview: 'Soft Text',
    category: 'Lifestyle',
    popularity: 82,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    textColor: '#334155',
    hasOutline: false,
    gradient: true
  }
]

export default function PresetSelector({ selectedPreset, onPresetChange, fontSize, onFontSizeChange, captionMode, onCaptionModeChange, showFiller, onShowFillerChange }: PresetSelectorProps) {
  const [hoveredPreset, setHoveredPreset] = useState<string | null>(null)

  const getPreviewStyle = (preset: typeof presets[0]) => {
    let style = {
      backgroundColor: preset.backgroundColor,
      color: preset.textColor,
      fontSize: `${fontSize * 0.6}px`, // Scale down for preview (60% of actual size)
      fontWeight: preset.id === 'highlight-bold' ? '800' : preset.id === 'neon-pop' ? '700' : '600',
      backdropFilter: preset.id === 'glass-glow' ? 'blur(8px)' : 'none',
      border: preset.hasOutline ? `2px solid ${preset.textColor}` : preset.id === 'glass-glow' ? '1px solid rgba(255, 255, 255, 0.3)' : 'none',
      textShadow: preset.hasOutline ? '2px 2px 0px #000000' : 'none',
      background: preset.gradient ? 'linear-gradient(135deg, rgba(255, 193, 204, 0.8), rgba(137, 255, 253, 0.8))' : preset.backgroundColor
    }
    return style
  }

  return (
    <div className="w-full">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-white mb-2">Choose Your Caption Style</h3>
        <p className="text-gray-400 text-sm">Select a style that matches your content vibe</p>
      </div>

      {/* Font Size Controls */}
      <div className="mb-8 p-6 bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h4 className="text-white font-semibold">Font Size</h4>
            <p className="text-gray-400 text-sm">Adjust caption size for your video</p>
          </div>
          <div className="bg-purple-500/20 px-3 py-1 rounded-lg">
            <span className="text-purple-300 font-bold">{fontSize}px</span>
          </div>
        </div>
        
        <div className="space-y-4">
          {/* Font Size Slider */}
          <div className="relative">
            <input
              type="range"
              min="16"
              max="72"
              step="2"
              value={fontSize}
              onChange={(e) => onFontSizeChange(Number(e.target.value))}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
              style={{
                background: `linear-gradient(to right, #8b5cf6 0%, #8b5cf6 ${((fontSize - 16) / (72 - 16)) * 100}%, #374151 ${((fontSize - 16) / (72 - 16)) * 100}%, #374151 100%)`
              }}
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>16px</span>
              <span>Small</span>
              <span>Medium</span>
              <span>Large</span>
              <span>72px</span>
            </div>
          </div>
          
          {/* Font Size Preview */}
          <div className="bg-gray-900 rounded-xl p-4 flex items-center justify-center min-h-[80px]">
            <div 
              className="px-4 py-2 rounded-lg font-bold text-center"
              style={getPreviewStyle(presets.find(p => p.id === selectedPreset) || presets[0])}
            >
              Sample Caption Text
            </div>
          </div>
        </div>
      </div>

      {/* Caption Mode Toggle */}
      <div className="mb-8 p-6 bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h4 className="text-white font-semibold">Caption Timing</h4>
            <p className="text-gray-400 text-sm">Choose how captions appear</p>
          </div>
          <div className="bg-blue-500/20 px-3 py-1 rounded-lg">
            <span className="text-blue-300 font-bold capitalize">{captionMode}</span>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Sentences Mode */}
          <div
            className={`relative border-2 rounded-xl p-4 cursor-pointer transition-all duration-300 ${
              captionMode === 'sentences'
                ? 'border-blue-400 bg-blue-500/10'
                : 'border-gray-600 bg-white/5 hover:border-gray-500 hover:bg-white/10'
            }`}
            onClick={() => onCaptionModeChange('sentences')}
          >
            <div className="flex items-center space-x-3">
              <div className={`w-5 h-5 rounded-full border-2 transition-all ${
                captionMode === 'sentences'
                  ? 'bg-blue-500 border-blue-500'
                  : 'border-gray-400'
              }`}>
                {captionMode === 'sentences' && (
                  <div className="w-2 h-2 bg-white rounded-full m-0.5"></div>
                )}
              </div>
              <div>
                <h5 className="text-white font-medium">Full Sentences</h5>
                <p className="text-gray-400 text-sm">Complete phrases appear together</p>
              </div>
            </div>
            <div className="mt-3 bg-gray-900 rounded-lg p-2 text-center">
              <div className="text-xs text-gray-300">"Hello, welcome to my video!"</div>
            </div>
          </div>

          {/* Words Mode */}
          <div
            className={`relative border-2 rounded-xl p-4 cursor-pointer transition-all duration-300 ${
              captionMode === 'words'
                ? 'border-purple-400 bg-purple-500/10'
                : 'border-gray-600 bg-white/5 hover:border-gray-500 hover:bg-white/10'
            }`}
            onClick={() => onCaptionModeChange('words')}
          >
            <div className="flex items-center space-x-3">
              <div className={`w-5 h-5 rounded-full border-2 transition-all ${
                captionMode === 'words'
                  ? 'bg-purple-500 border-purple-500'
                  : 'border-gray-400'
              }`}>
                {captionMode === 'words' && (
                  <div className="w-2 h-2 bg-white rounded-full m-0.5"></div>
                )}
              </div>
              <div>
                <h5 className="text-white font-medium">Word-by-Word</h5>
                <p className="text-gray-400 text-sm">Karaoke-style pop-up words</p>
              </div>
            </div>
            <div className="mt-3 bg-gray-900 rounded-lg p-2 text-center">
              <div className="text-xs text-gray-300">"Hello" → "welcome" → "to"</div>
            </div>
          </div>
        </div>

        {/* Show Filler Words Toggle (only visible in words mode) */}
        {captionMode === 'words' && (
          <div className="mt-4 p-4 bg-white/5 backdrop-blur-sm rounded-xl border border-white/10">
            <div className="flex items-center justify-between">
              <div>
                <h5 className="text-white font-medium">Show Filler Words</h5>
                <p className="text-gray-400 text-sm">Include "the", "and", "is" etc. (with reduced opacity)</p>
              </div>
              <div className="flex items-center space-x-3">
                <span className={`text-sm ${showFiller ? 'text-gray-400' : 'text-green-400 font-medium'}`}>
                  Clean
                </span>
                <button
                  onClick={() => onShowFillerChange(!showFiller)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    showFiller ? 'bg-purple-600' : 'bg-gray-600'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      showFiller ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
                <span className={`text-sm ${showFiller ? 'text-purple-400 font-medium' : 'text-gray-400'}`}>
                  All Words
                </span>
              </div>
            </div>
            
            {/* Filler Words Explanation */}
            <div className="mt-3 p-3 bg-gray-700/20 rounded-lg">
              <div className="flex items-start space-x-2">
                <div className="w-4 h-4 bg-purple-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg className="w-2 h-2 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="text-sm">
                  {showFiller ? (
                    <p className="text-gray-300">
                      <span className="text-purple-300 font-medium">All Words Mode:</span> Shows every word including "the", "and", "is" with reduced opacity for context while keeping focus on key words.
                    </p>
                  ) : (
                    <p className="text-gray-300">
                      <span className="text-green-300 font-medium">Clean Mode:</span> Shows only important words like nouns, verbs, and adjectives. Perfect for impact and readability.
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Mode Description */}
        <div className="mt-4 p-3 bg-gray-700/20 rounded-lg">
          <div className="flex items-start space-x-2">
            <div className="w-4 h-4 bg-yellow-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
              <svg className="w-2 h-2 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="text-sm">
              {captionMode === 'sentences' ? (
                <p className="text-gray-300">
                  <span className="text-blue-300 font-medium">Full Sentences:</span> Best for tutorials, vlogs, and narrative content. 
                  Easier to read with natural pacing.
                </p>
              ) : (
                <p className="text-gray-300">
                  <span className="text-purple-300 font-medium">Word-by-Word:</span> Perfect for music videos, dramatic content, and emphasis. 
                  Creates engaging karaoke-style effects.
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {presets.map((preset) => (
          <div
            key={preset.id}
            className={`relative group border-2 rounded-2xl p-6 cursor-pointer transition-all duration-300 transform hover:scale-105 ${
              selectedPreset === preset.id
                ? 'border-purple-400 bg-purple-500/10 shadow-lg shadow-purple-500/25'
                : 'border-gray-600 bg-white/5 hover:border-gray-500 hover:bg-white/10'
            }`}
            onClick={() => onPresetChange(preset.id)}
            onMouseEnter={() => setHoveredPreset(preset.id)}
            onMouseLeave={() => setHoveredPreset(null)}
          >
            {/* Popularity Badge */}
            <div className="absolute -top-2 -right-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white text-xs font-bold px-2 py-1 rounded-full">
              {preset.popularity}% ❤️
            </div>

            <div className="space-y-4">
              {/* Header */}
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-bold text-white text-lg">{preset.name}</h4>
                  <span className="text-xs text-gray-400 bg-gray-700/50 px-2 py-1 rounded-full">
                    {preset.category}
                  </span>
                </div>
                <div className={`w-6 h-6 rounded-full border-2 transition-all ${
                  selectedPreset === preset.id
                    ? 'bg-purple-500 border-purple-500 scale-110'
                    : 'border-gray-400'
                }`}>
                  {selectedPreset === preset.id && (
                    <div className="w-3 h-3 bg-white rounded-full m-0.5"></div>
                  )}
                </div>
              </div>
              
              {/* Preview */}
              <div className="relative">
                <div className="bg-gray-900 rounded-xl p-4 aspect-video flex items-center justify-center relative overflow-hidden">
                  {/* Simulated video background */}
                  <div className="absolute inset-0 bg-gradient-to-br from-gray-800 to-gray-900 opacity-50"></div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="w-16 h-16 border-4 border-gray-600 rounded-full opacity-20"></div>
                  </div>
                  
                  {/* Caption preview */}
                  <div 
                    className="relative z-10 px-4 py-2 rounded-lg text-center font-bold text-lg"
                    style={getPreviewStyle(preset)}
                  >
                    {preset.preview}
                  </div>
                </div>
                
                {hoveredPreset === preset.id && (
                  <div className="absolute inset-0 bg-purple-500/20 rounded-xl flex items-center justify-center">
                    <div className="bg-black/50 text-white px-3 py-1 rounded-full text-sm font-medium">
                      Click to select
                    </div>
                  </div>
                )}
              </div>
              
              {/* Description */}
              <p className="text-sm text-gray-400 leading-relaxed">{preset.description}</p>
              
              {/* Features */}
              <div className="flex flex-wrap gap-2">
                {preset.hasOutline && (
                  <span className="text-xs bg-gray-700/50 text-gray-300 px-2 py-1 rounded-full">
                    Outlined
                  </span>
                )}
                {preset.gradient && (
                  <span className="text-xs bg-gray-700/50 text-gray-300 px-2 py-1 rounded-full">
                    Gradient
                  </span>
                )}
                <span className="text-xs bg-gray-700/50 text-gray-300 px-2 py-1 rounded-full">
                  Auto-sync
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Style Tips */}
      <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl">
        <div className="flex items-start space-x-3">
          <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
            <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h4 className="text-blue-300 font-medium text-sm mb-1">Pro Tip</h4>
            <p className="text-blue-200/80 text-sm">
              {selectedPreset === 'highlight-bold' && "Perfect for tutorial content and call-to-actions. Works great on all platforms."}
              {selectedPreset === 'neon-pop' && "Ideal for gaming clips, memes, and high-energy content. Grabs attention instantly."}
              {selectedPreset === 'glass-glow' && "Best for lifestyle, beauty, and aesthetic content. Creates a premium feel."}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}