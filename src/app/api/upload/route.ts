import { NextRequest, NextResponse } from 'next/server'
import { writeFile, mkdir } from 'fs/promises'
import { existsSync } from 'fs'
import { spawn } from 'child_process'
import path from 'path'
import { v4 as uuidv4 } from 'uuid'
import { jobs } from '@/lib/jobs'

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get('video') as File
    const preset = formData.get('preset') as string
    const fontSizeStr = formData.get('fontSize') as string
    const captionMode = formData.get('captionMode') as string
    const showFillerStr = formData.get('showFiller') as string

    if (!file) {
      return NextResponse.json({ error: 'No file uploaded' }, { status: 400 })
    }

    // Validate and parse fontSize
    const fontSize = parseInt(fontSizeStr) || 42 // Default to 42 if not provided
    if (fontSize < 16 || fontSize > 72) {
      return NextResponse.json({ error: 'Font size must be between 16 and 72 pixels' }, { status: 400 })
    }

    // Validate captionMode
    const validCaptionModes = ['sentences', 'words']
    const validatedCaptionMode = validCaptionModes.includes(captionMode) ? captionMode : 'sentences'

    // Validate showFiller
    const showFiller = showFillerStr === 'true'

    // Validate file
    const allowedTypes = ['video/mp4', 'video/quicktime', 'video/webm']
    if (!allowedTypes.includes(file.type)) {
      return NextResponse.json({ error: 'Invalid file type' }, { status: 400 })
    }

    if (file.size > 120 * 1024 * 1024) { // 120MB
      return NextResponse.json({ error: 'File too large' }, { status: 400 })
    }

    // Generate job ID and create directory
    const jobId = uuidv4()
    const jobDir = path.join(process.cwd(), 'tmp', 'jobs', jobId)
    
    if (!existsSync(jobDir)) {
      await mkdir(jobDir, { recursive: true })
    }

    // Save file
    const bytes = await file.arrayBuffer()
    const buffer = Buffer.from(bytes)
    const fileExtension = path.extname(file.name)
    const filePath = path.join(jobDir, `input${fileExtension}`)
    
    await writeFile(filePath, buffer)

    // Initialize job status
    jobs.set(jobId, {
      status: 'pending',
      progress: 0,
      createdAt: new Date()
    })
    
    console.log(`Job ${jobId} created and stored. Total jobs: ${jobs.size}`)

    // Start Python worker
    processVideo(jobId, filePath, preset || 'highlight-bold', fontSize, validatedCaptionMode, showFiller)

    return NextResponse.json({ jobId })
  } catch (error) {
    console.error('Upload error:', error)
    return NextResponse.json({ error: 'Upload failed' }, { status: 500 })
  }
}

async function processVideo(jobId: string, inputFile: string, preset: string, fontSize: number, captionMode: string, showFiller: boolean) {
  try {
    console.log(`Starting processing for job ${jobId} with preset ${preset}, font size ${fontSize}px, caption mode: ${captionMode}, showFiller: ${showFiller}`)
    
    // Update job status
    const job = jobs.get(jobId)
    if (job) {
      job.status = 'processing'
      job.progress = 10
    }

    // Choose worker based on caption mode - use enterprise for words mode
    const workerScript = captionMode === 'words' ? 'main_enterprise.py' : 'main.py'
    const workerArgs = captionMode === 'words' ? [
      path.join(process.cwd(), 'worker', workerScript),
      jobId,
      preset,
      inputFile,
      fontSize.toString(),
      captionMode,
      showFiller.toString()
    ] : [
      path.join(process.cwd(), 'worker', workerScript),
      jobId,
      preset,
      inputFile,
      fontSize.toString(),
      captionMode
    ]

    // Run Python worker (use conda python where SpaCy is installed)
    const workerProcess = spawn('python', workerArgs)

    workerProcess.stdout.on('data', (data) => {
      const output = data.toString()
      console.log(`Worker output: ${output}`)
      
      // Parse progress updates
      if (output.includes('PROGRESS:')) {
        const progress = parseInt(output.match(/PROGRESS:(\d+)/)?.[1] || '0')
        const job = jobs.get(jobId)
        if (job) {
          job.progress = progress
        }
      }
    })
    
    workerProcess.stderr.on('data', (data) => {
      console.error(`Worker error: ${data}`)
    })
    
    workerProcess.on('close', (code) => {
      const job = jobs.get(jobId)
      if (!job) return

      if (code === 0) {
        // Success - check for output file
        const outputFile = path.join(process.cwd(), 'output', `${jobId}_captioned.mp4`)
        if (existsSync(outputFile)) {
          job.status = 'completed'
          job.progress = 100
          job.downloadUrl = `/output/${jobId}_captioned.mp4`
          console.log(`Job ${jobId} completed successfully`)
        } else {
          job.status = 'error'
          job.error = 'Output file not found'
          console.error(`Job ${jobId} failed: Output file not found`)
        }
      } else {
        job.status = 'error'
        job.error = `Processing failed with code ${code}`
        console.error(`Job ${jobId} failed with exit code ${code}`)
      }
    })
    
  } catch (error) {
    console.error('Processing error:', error)
    const job = jobs.get(jobId)
    if (job) {
      job.status = 'error'
      job.error = error instanceof Error ? error.message : 'Unknown error'
    }
  }
}

