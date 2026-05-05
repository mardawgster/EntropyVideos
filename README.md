# Entropy Lab

A multi-video entropy analysis tool that calculates Shannon, Rényi, and Tsallis entropy metrics for video frames in real-time. Includes a video preprocessing utility for cropping and frame decimation.

## 📋 Project Structure

```
EntropyVideos/
├── crop.py                          # Video preprocessing tool
├── entropy-lab/
│   ├── backend/
│   │   └── main.py                 # FastAPI server
│   └── frontend/
│       ├── src/
│       │   └── App.jsx             # React application
│       ├── package.json
│       └── vite.config.js
└── OscilattingTool/
    ├── Originals/                  # Raw video files
    └── Modified/                   # Processed videos
```

## 🔧 Prerequisites

### System Requirements
- Python 3.8+
- Node.js 14+
- FFmpeg (for video processing)

### macOS Installation
```bash
# Install FFmpeg
brew install ffmpeg
```

### Linux Installation
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# Fedora
sudo dnf install ffmpeg
```

## 📦 Installation

### 1. Clone/Setup Repository
```bash
cd /Users/marcusdibattista/EntropyVideos
```

### 2. Setup Backend

#### Create Python Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows
```

#### Install Python Dependencies
```bash
pip install fastapi uvicorn opencv-python numpy scipy python-multipart
```

### 3. Setup Frontend

```bash
cd entropy-lab/frontend
npm install
```

## 🚀 Usage

### Video Preprocessing (crop.py)

The `crop.py` utility processes multiple videos in batch with cropping and frame decimation.

#### Configuration
Edit the `crop_video()` function call parameters in `crop.py`:

```python
crop_video(
    input_path,           # Input video path
    output_path,          # Output video path
    crop_width=1504,      # Crop width in pixels (default: 1504)
    crop_height=1800,     # Crop height in pixels (default: 1800)
    bitrate=3000,         # Output bitrate in kbps (default: 3000)
    x_offset=None,        # Horizontal offset (None = center)
    y_offset=120,         # Vertical offset from top (default: 120)
    frame_step=3          # Output 1 frame per N frames (default: 3)
)
```

#### Offset Guide
- `x_offset=None` - Center horizontally
- `x_offset=0` - Crop from left edge
- `x_offset=100` - Shift crop 100px to the right
- `y_offset=None` - Center vertically
- `y_offset=0` - Crop from top edge
- `y_offset=120` - Shift crop 120px down

#### Run Batch Processing
```bash
python crop.py
```

The script will:
1. Find all `.mp4` files in `OscilattingTool/Originals/`
2. Process each video with crop/decimate settings
3. Save to `OscilattingTool/Modified/` with `_mod.mp4` suffix

### Entropy Analysis (Entropy Lab)

#### Start Backend Server
```bash
cd entropy-lab/backend
source ../../venv/bin/activate  # If using venv
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at: `http://localhost:8000`

#### Start Frontend Development Server
In a new terminal:
```bash
cd entropy-lab/frontend
npm run dev
```

Frontend will be available at: `http://localhost:5173` (or shown in terminal output)

#### Using the Interface

1. **Queue Videos**: Click "Add Videos" to upload multiple MP4 files
2. **Select Algorithms**: Choose which entropy metrics to calculate:
   - **Shannon Entropy** - Standard information entropy
   - **Rényi Entropy** - Generalized entropy (α parameter)
   - **Tsallis Entropy** - Non-extensive entropy (q parameter)
3. **Run Analysis**: Click "Run Analysis 🚀" to process all queued videos
4. **View Results**: 
   - Graphs show comparative entropy streams
   - Click on graph to sync video playback
   - Video player shows real-time analysis overlay

## 📊 API Endpoints

### POST `/analyze-entropy`

Analyzes entropy metrics for an uploaded video.

**Parameters:**
- `file` (UploadFile): Video file (MP4)
- `n_frame` (int): Analyze every Nth frame (default: 10)
- `alpha` (float): Rényi entropy parameter (default: 2.0)
- `q` (float): Tsallis entropy parameter (default: 2.0)
- `roi` (str): Region of interest as JSON array `[x, y, width, height]` (default: `[0, 0, 500, 500]`)
- `calc_shannon` (bool): Calculate Shannon entropy
- `calc_renyi` (bool): Calculate Rényi entropy
- `calc_tsallis` (bool): Calculate Tsallis entropy

**Response:**
```json
{
  "data": [
    {
      "time": 0.0,
      "shannon": 7.234,
      "renyi": 6.891,
      "tsallis": 0.523
    }
  ],
  "fps": 30.0
}
```

## 🔍 Example Workflows

### Workflow 1: Preprocess Videos
```bash
# Edit crop.py with desired settings
# Set frame_step=3 for 3x speed reduction
# Set y_offset=120 to skip top portion
python crop.py
# Videos saved to OscilattingTool/Modified/
```

### Workflow 2: Analyze Multiple Videos
1. Start backend: `python -m uvicorn main:app --reload`
2. Start frontend: `npm run dev`
3. Open browser to `http://localhost:5173`
4. Upload preprocessed videos from `OscilattingTool/Modified/`
5. Select algorithms and run analysis
6. Compare entropy streams across videos

## ⚙️ Troubleshooting

### FFmpeg Not Found
```bash
# Verify FFmpeg is installed
ffmpeg -version

# If not installed, install via package manager (see Prerequisites)
```

### CORS Errors
Backend already has CORS middleware enabled for all origins. If issues persist, check that backend is running on `http://localhost:8000`

### Slow Analysis
- Increase `n_frame` parameter (e.g., 20 instead of 10) to analyze fewer frames
- Use smaller ROI to reduce calculation area
- Preprocess videos with higher `frame_step` value

### Port Already in Use
```bash
# Change backend port
python -m uvicorn main:app --port 8001

# Change frontend port (auto-detected if 5173 is busy)
npm run dev
```

## 📝 Notes

- Videos are processed in-memory and deleted after analysis
- Maximum recommended video duration: 5 minutes (depends on frame sampling)
- Entropy values depend on histogram distribution of ROI
- Frame decimation (frame_step) reduces output video duration proportionally

## 🛠️ Development

To modify entropy calculations, edit the functions in `entropy-lab/backend/main.py`:
- `calculate_shannon()` - Shannon entropy
- `calculate_renyi()` - Rényi entropy with parameter α
- `calculate_tsallis()` - Tsallis entropy with parameter q
