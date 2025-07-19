const express = require('express')
const multer = require('multer')
const cors = require('cors')
const { v4: uuidv4 } = require('uuid')
const path = require('path')
const fs = require('fs')
const { spawn } = require('child_process')

const app = express()
const PORT = process.env.PORT || 3001

// Middleware
app.use(cors())
app.use(express.json())

// File upload configuration
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const jobId = req.body.jobId || uuidv4()
    const jobDir = path.join(__dirname, '../tmp/jobs', jobId)
    
    if (!fs.existsSync(jobDir)) {
      fs.mkdirSync(jobDir, { recursive: true })
    }
    
    req.jobId = jobId
    cb(null, jobDir)
  },
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname)
    cb(null, `input${ext}`)
  }
})

const upload = multer({
  storage,
  limits: {
    fileSize: 120 * 1024 * 1024, // 120MB limit
  },
  fileFilter: (req, file, cb) => {
    const allowedTypes = ['video/mp4', 'video/quicktime', 'video/webm']
    if (allowedTypes.includes(file.mimetype)) {
      cb(null, true)
    } else {
      cb(new Error('Only MP4, MOV, and WEBM files are allowed'))
    }
  }
})

// In-memory job storage
const jobs = new Map()

// Routes
app.post('/api/upload', upload.single('video'), (req, res) => {
  try {
    const jobId = req.jobId || uuidv4()
    const preset = req.body.preset || 'highlight-bold'
    const filePath = req.file.path
    
    // Initialize job status
    jobs.set(jobId, {
      status: 'pending',
      progress: 0,
      preset,
      inputFile: filePath,
      createdAt: new Date()
    })
    
    // Start processing
    processVideo(jobId, filePath, preset)
    
    res.json({ jobId })
  } catch (error) {
    console.error('Upload error:', error)
    res.status(500).json({ error: 'Upload failed' })
  }
})

app.get('/api/status/:jobId', (req, res) => {
  const { jobId } = req.params
  const job = jobs.get(jobId)
  
  if (!job) {
    return res.status(404).json({ error: 'Job not found' })
  }
  
  res.json({
    status: job.status,
    progress: job.progress,
    error: job.error,
    downloadUrl: job.downloadUrl
  })
})

// Serve static files from output directory
app.use('/output', express.static(path.join(__dirname, '../output')))

async function processVideo(jobId, inputFile, preset) {
  try {
    // Update job status
    jobs.set(jobId, { ...jobs.get(jobId), status: 'processing', progress: 10 })
    
    // Run Python worker
    const workerProcess = spawn('python3', [
      path.join(__dirname, '../worker/main.py'),
      jobId,
      preset,
      inputFile
    ])
    
    workerProcess.stdout.on('data', (data) => {
      const output = data.toString()
      console.log(`Worker output: ${output}`)
      
      // Parse progress updates
      if (output.includes('PROGRESS:')) {
        const progress = parseInt(output.match(/PROGRESS:(\d+)/)?.[1] || '0')
        jobs.set(jobId, { ...jobs.get(jobId), progress })
      }
    })
    
    workerProcess.stderr.on('data', (data) => {
      console.error(`Worker error: ${data}`)
    })
    
    workerProcess.on('close', (code) => {
      if (code === 0) {
        // Success - check for output file
        const outputFile = path.join(__dirname, '../output', `${jobId}_captioned.mp4`)
        if (fs.existsSync(outputFile)) {
          jobs.set(jobId, {
            ...jobs.get(jobId),
            status: 'completed',
            progress: 100,
            downloadUrl: `/output/${jobId}_captioned.mp4`
          })
        } else {
          jobs.set(jobId, {
            ...jobs.get(jobId),
            status: 'error',
            error: 'Output file not found'
          })
        }
      } else {
        jobs.set(jobId, {
          ...jobs.get(jobId),
          status: 'error',
          error: `Processing failed with code ${code}`
        })
      }
    })
    
  } catch (error) {
    console.error('Processing error:', error)
    jobs.set(jobId, {
      ...jobs.get(jobId),
      status: 'error',
      error: error.message
    })
  }
}

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`)
})