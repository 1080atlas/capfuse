# MVP Caption‑Burner Web App

A concise reference for building a **drag‑and‑drop caption studio** with three preset styles.  Use this file while coding, testing, and launching your Wizard‑of‑Oz experiment.

---

## 1 · Product Overview

| Aspect                 | Detail                                                                                      |
| ---------------------- | ------------------------------------------------------------------------------------------- |
| **Primary user (MVP)** | **You** on your Mac (single‑user localhost)                                                 |
| **Core promise**       | “Drag a clip onto `http://localhost:3000`, pick a style, get a captioned MP4 in `/Output`.” |
| **Clip limits**        | ≤ 120 MB • ≤ 60 s • MP4 / MOV / WEBM                                                        |
| **Persistence**        | Files stay only on your disk (`./tmp` + `./output`). No cloud storage, no DB.               |
| **Future expansion**   | Swap local `/tmp` + `mem` queue for S3 + Vercel Blob; add auth + Stripe later.              |

\--------|--------|
\| **Primary user** | Short‑form video creator (TikTok / Reels / Shorts) |
\| **Core promise** | “Upload a clip, pick a style, get a captioned MP4 in minutes.” |
\| **Clip limits** | ≤ 120 MB • ≤ 60 s • MP4 / MOV / WEBM |
\| **Outputs** | 1080 × 1920 MP4 (20 Mb/s) + optional SRT download |
\| **Monetisation (post‑MVP)** | Free 30 s watermarked · \$15/mo Creator · \$49/mo Pro |

---

## 2 · End‑to‑End User Flow

```text
┌───────────┐   1 drag‑drop   ┌────────────┐   2 choose   ┌────────────┐
│  Browser  │───────────────▶│  Upload API │────────────▶│   Waiting   │
└───────────┘                └────────────┘              │  progress   │
     ▲                            ▲                      │  polling    │
     │ 5 download                 │                      └────┬───────┘
┌────┴───────┐   4 presigned URL  │ 3 job queued              │
│  S3 / tmp  │◀───────────────────┘                           │
└────────────┘                                                ▼
                                            ┌────────────────────────┐
                                            │ Python worker:         │
                                            │  • Whisper‑cpp → SRT   │
                                            │  • ASS style inject    │
                                            │  • ffmpeg burn‑in      │
                                            └────────────────────────┘
```

---

## 3 · System Architecture

### 3.1 Front‑end (Next.js 14)

* **Pages** : `/` (upload + presets)  ·  `/done` (download)
* **Components** : `DragDrop`, `PresetSelector`, `ProgressBar`
* **State** : React Query polling `GET /status/:jobId`

### 3.2 Back‑end (Node 18 + Express)

| Route                | Purpose                                   |
| -------------------- | ----------------------------------------- |
| `POST /upload`       | Save file → create `jobId` → spawn worker |
| `GET /status/:jobId` | Return `{ progress, error?, url? }`       |
| Static               | Serves built Next.js + preset JSON        |

### 3.3 Worker (Python 3.11)

1. `whisper.cpp` → `clip.srt` (auto‑detect lang)
2. Build `clip.ass` using selected preset JSON.
3. `ffmpeg` burn: `-vf "subtitles=clip.ass"` → `clip_captioned.mp4`.
4. Upload to S3 (or move to `/tmp` in dev).

### 3.4 Storage

* **Dev** : local `/tmp/jobs/<jobId>`
* **Prod** : S3 bucket + pre‑signed GET (1 day)

### 3.5 Deployment (Vercel)

* **Target** : Vercel – front‑end, API routes, and background tasks.
* **Front‑end & API** : Next.js pages + `/api` functions run as Vercel Serverless Functions.
* **Worker** : Vercel Background Function (`vercel.json` → `runtime:"python"`) that executes Whisper + ffmpeg, then uploads to Blob Storage (or S3).
* **Storage** : Use Vercel Blob for small clips; switch to S3 when you exceed limits.
* **Local dev** : `docker-compose` remains for offline testing.

---

## 4 · Caption Style Presets  (July 2025 trendy but not over‑the‑top)

| ID               | Look & purpose                                                                              | Font                 | Size  | Fill                       | Accent                               | Animation       |
| ---------------- | ------------------------------------------------------------------------------------------- | -------------------- | ----- | -------------------------- | ------------------------------------ | --------------- |
| `highlight-bold` | **Modern creator standard** – bold white on TikTok‑yellow bar; grabs eyes without screaming | Montserrat ExtraBold | 42 px | White                      | Highlight bar #FFE600 (70 % opacity) | Fade‑in 0.15 s  |
| `neon-pop`       | **Gaming / meme hype** – letter‑boxed neon text with soft glow; good for punchlines         | BebasNeue            | 50 px | #2BFF88                    | 3 px black outline + glow            | Scale‑up 0.3 s  |
| `glass-glow`     | **Lifestyle / vlog chic** – frosted‑glass transparent box + soft pastel gradient text       | Poppins SemiBold     | 40 px | Gradient #FFC1CC → #89FFFD | 1 px white outline; backdrop blur 6  | Slide‑up 0.25 s |

### JSON for `preset_styles.json`

```json
[
  {
    "id": "highlight-bold",
    "font": "Montserrat-ExtraBold",
    "fontSize": 42,
    "primaryColour": "&H00FFFFFF",
    "backColour": "&H70E6FF00",  // 70% TikTok yellow
    "outlineColour": "&H00000000",
    "outline": 0,
    "shadow": 0,
    "animation": "in:fade=0.15"
  },
  {
    "id": "neon-pop",
    "font": "BebasNeue",
    "fontSize": 50,
    "primaryColour": "&H0088FF2B",  // neon green
    "outlineColour": "&H00000000",
    "outline": 3,
    "shadow": 0,
    "shadowColour": "&H00000000",
    "animation": "in:scale=1.3,duration=0.3"
  },
  {
    "id": "glass-glow",
    "font": "Poppins-SemiBold",
    "fontSize": 40,
    "primaryColour": "&H00FFCCFF",  // pastel gradient simulated by overlay (ffmpeg drawbox layer)
    "outlineColour": "&H00FFFFFF",
    "outline": 1,
    "shadow": 0,
    "backColour": "&H40FFFFFF",  // 25% white for glass effect
    "animation": "in:slideup=0.25"
  }
]
```

\----|------|------|------|---------|--------|-----------|
\| `clean` | OpenSans‑Bold | 40 px | White | 1 px black | none | none |
\| `neon-pop` | BebasNeue | 48 px | #33FF66 | 3 px black | none | Pop‑in 0.3 s |
\| `soft-vlog` | Poppins‑Medium | 38 px | White | 0 | Blur 4, 50 % | none |
*Store these in `preset_styles.json`; worker reads style block → ASS `Style:` line.*

---

## 5 · Build Roadmap (target ≤ 8 hrs)

| Hr  | Milestone       | Key tasks                                    |
| --- | --------------- | -------------------------------------------- |
| 1   | Skeleton        | Next.js page • Express scaffold • Dockerfile |
| 2   | Upload API      | `multer` file save • return `jobId`          |
| 3   | Polling UI      | React Query hook • progress bar              |
| 4–5 | Python worker   | Whisper call • ASS gen • ffmpeg burn         |
| 6   | Presigned URLs  | Local vs S3 toggle                           |
| 7   | Style presets   | JSON read • three ASS templates              |
| 8   | README + deploy | Railway Docker deploy • test with 3 clips    |

---

## 6 · Launch Checklist (Wizard‑of‑Oz)

* [ ] Deploy to Railway
* [ ] Test three styles with sample clips (Eng / Nor / noisy)
* [ ] Create r/NewTubers post offering free caption service
* [ ] Monitor `docker logs -f` for failures; re‑queue as needed
* [ ] Log feedback in Google Sheet (`style`, `quality`, `turnaround`)
* [ ] If 70 %+ positive, proceed to Stripe + auth phase

---

## 7 · Key Commands

```bash
# Dev
npm run dev          # Next.js
node server/index.js # API
python worker/main.py jobId preset file.mp4

# Build & run all
docker-compose up --build
```

---

## 8 · Resources

* Whisper‑cpp repo – [https://github.com/ggerganov/whisper.cpp](https://github.com/ggerganov/whisper.cpp)
* ffmpeg burn‑in docs – `man ffmpeg-filters` (`subtitles`)
* Next.js deployment guide – [https://nextjs.org/docs/deployment](https://nextjs.org/docs/deployment)

---

*End of brief — keep this file open while coding.*
