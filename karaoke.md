# Enterprise‑Grade Word‑by‑Word (Karaoke) Caption System

Stand‑alone engineering brief. Paste sections 2‑7 into Claude (or follow manually) when you are ready to evolve CapFuse’s word‑level captions from MVP to production quality **with a “Show filler words” toggle**.

---

## 1 Goals

| # | Requirement                                                                                                       |
| - | ----------------------------------------------------------------------------------------------------------------- |
| 1 | Frame‑accurate word timing ≤ 35 ms avg error on > 95 % of clips ≤ 120 s                                           |
| 2 | Optional context‑aware filtering – keep semantically important stop words **unless the user opts to include all** |
| 3 | Dynamic visuals – active‑word highlight, fade, alternating Y‑pos to reduce OLED burn‑in                           |
| 4 | Parallel scalability – 4 concurrent jobs on one M‑series Mac; easy cloud lift                                     |
| 5 | Deterministic builds; unit + integration tests, reproducible Docker images                                        |

---

## 2 Pipeline Overview

```text
Video ▶ Audio (FFmpeg) ▶ Whisper‑cpp JSON ▶ Gentle forced alignment ▶
Filter (SpaCy POS) ▶ Timing smoother ▶ ASS builder ▶ FFmpeg burn‑in
```

*Filter step is **skipped** when `showFiller = true` (user wants every word).*
*When skipped, filler words render using the inactive style so they are visually de‑emphasised but still present.*

---

## 3 Component Details

### 3.1 Audio Extraction

```bash
ffmpeg -i clip.mp4 -vn -ac 1 -ar 16000 -c:a pcm_s16le tmp.wav
```

### 3.2 Automatic Speech Recognition

```bash
whisper-cli -m ggml-small.bin -oj tmp.json   # includes per‑word timestamps
```

### 3.3 Forced Alignment (Tighten Timing)

* **Tool** : Gentle (Kaldi) Docker image [https://github.com/lowerquality/gentle](https://github.com/lowerquality/gentle)
* **Call** :

```bash
curl -F "audio=@tmp.wav" -F "transcript=@tmp.json" \
     gentle:8765/transcriptions?async=false > aligned.json
```

* Achieve ≤ 35 ms word‑start error.

### 3.4 Smart Word Filtering

| Scenario             | Action                                                                                                                                 |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `showFiller = false` | Run SpaCy pipeline, drop filler tokens (articles, auxiliaries, interjections) except when required in idioms or ≤ 2‑word noun phrases. |
| `showFiller = true`  | **Bypass filter**; mark fillers with attribute `inactive=true` for later styling.                                                      |

### 3.5 Timing Smoothing

```python
MIN_DUR = 0.45  # seconds, guarantee readability
gap_merge = 0.10  # merge gaps shorter than 100 ms
```

Clamp last word ≤ clip length.

### 3.6 ASS Subtitle Generation

* **Styles**

  * `WordActive` – 100 % white, scale 110 %, fade 100 ms
  * `WordInactive` – 50 % white, scale 100 %
* **Logic** :

  * For each word:

    * Use karaoke tag `{\k<centisec>}` to drive activation.
    * Apply `WordInactive` style by default.
    * If token `inactive=false`, wrap with `\rWordActive \N` during its active window.
* **Layout** : Center horizontally; alternate `posY` 860 ↔ 900 every 8 words.

### 3.7 Burn‑in

```bash
ffmpeg -i clip.mp4 \
  -vf "subtitles=styled.ass:fontsdir=/app/fonts" \
  -c:v libx264 -crf 21 -preset veryfast -c:a copy out.mp4
```

Hardware: VideoToolbox acceleration on macOS.

---

## 4 Code Layout

| Path                    | Purpose                                               |
| ----------------------- | ----------------------------------------------------- |
| `worker/alignment.py`   | Gentle wrapper (`align(json)->json`)                  |
| `worker/filters.py`     | SpaCy POS; exports `filter_words(words, show_filler)` |
| `worker/timing.py`      | Smoothing helpers (unit‑tested)                       |
| `worker/ass_builder.py` | Build dynamic ASS w/ karaoke tags                     |
| `tests/`                | Pytest fixtures (8) run < 60 s                        |

---

## 5 API Changes

| Param         | Values       | Behaviour     |                                                                                                                             |
| ------------- | ------------ | ------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `captionMode` | `sentences`  |  `words`      | Sentence vs karaoke (existing)                                                                                              |
| `precision`   | `mvp`        |  `enterprise` | Fast vs full alignment                                                                                                      |
| `showFiller`  | `true`       |  `false`      | **New** – When `false`, filter step removes fillers; `true` keeps every word but renders fillers with `WordInactive` style. |

Front‑end: add toggle labelled **“Show filler words”**; default `false`.

Worker CLI flag:

```bash
python worker/main.py --job $ID --preset $PRESET \
     --precision $PRECISION --show-filler $SHOWFILLER
```

---

## 6 Performance Targets

| Metric             | Goal                                                |
| ------------------ | --------------------------------------------------- |
| 60 s clip (M1 Air) | < 30 s total (ASR 18 s, alignment 4 s, burn‑in 6 s) |
| Peak RAM           | < 1.2 GB                                            |

---

## 7 Deliverables

1. Python modules & unit tests covering both `showFiller` branches.
2. Two CLI samples:

   * `./run_local.sh clip.mp4 neon-pop enterprise false` (hide fillers)
   * `./run_local.sh clip.mp4 neon-pop enterprise true` (show fillers)
3. README updates: Gentle Docker, font dirs, benchmark, filler‑toggle description.

---

*Save this file alongside the MVP brief.  Feed Sections 2‑7 to Claude when you’re ready to implement the enterprise‑grade word‑by‑word system with optional filler‑word display.*
