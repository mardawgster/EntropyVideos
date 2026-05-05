import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import PlotComponent from 'react-plotly.js';

// Unwrap Plotly to avoid Vite caching bugs
const Plot = PlotComponent.default || PlotComponent;

export default function App() {
  // Setup State
  const [videoQueue, setVideoQueue] = useState([]);
  const [metrics, setMetrics] = useState({ shannon: true, renyi: true, tsallis: true });
  const [analysisResults, setAnalysisResults] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  
  // Playback State
  const [activeVideoIndex, setActiveVideoIndex] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const videoRef = useRef(null);

  // --- Queue Management ---
  const handleAddFiles = (e) => {
    const files = Array.from(e.target.files);
    const newVideos = files.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      file: file,
      url: URL.createObjectURL(file),
      name: file.name
    }));
    setVideoQueue(prev => [...prev, ...newVideos]);
  };

  const removeVideo = (idToRemove) => {
    setVideoQueue(prev => prev.filter(v => v.id !== idToRemove));
    if (analysisResults.length > 0) {
       setAnalysisResults(prev => prev.filter(v => v.id !== idToRemove));
    }
  };

  const toggleMetric = (metric) => {
    setMetrics(prev => ({ ...prev, [metric]: !prev[metric] }));
  };

  // --- API Communication ---
  const handleAnalyze = async () => {
    if (videoQueue.length === 0) return;
    setIsProcessing(true);
    setAnalysisResults([]); // Clear old results

    try {
      // Process all videos concurrently
      const promises = videoQueue.map(async (video) => {
        const formData = new FormData();
        formData.append('file', video.file);
        formData.append('n_frame', 10);
        formData.append('alpha', 2.0);
        formData.append('q', 2.0);
        formData.append('roi', JSON.stringify([0, 0, 500, 500]));
        formData.append('calc_shannon', metrics.shannon);
        formData.append('calc_renyi', metrics.renyi);
        formData.append('calc_tsallis', metrics.tsallis);

        const response = await axios.post('http://localhost:8000/analyze-entropy', formData);
        return { 
          id: video.id, 
          name: video.name, 
          data: response.data.data 
        };
      });

      const results = await Promise.all(promises);
      setAnalysisResults(results);
      setActiveVideoIndex(0); // Reset preview to the first video
    } catch (error) {
      console.error("Error analyzing videos:", error);
      alert("Failed to analyze videos. Check console for details.");
    } finally {
      setIsProcessing(false);
    }
  };

  // --- Graph & Sync Logic ---
  const handleTimeUpdate = () => {
    if (videoRef.current) setCurrentTime(videoRef.current.currentTime);
  };

  const handleChartClick = (data) => {
    if (data.points && data.points.length > 0 && videoRef.current) {
      const clickedTime = data.points[0].x;
      videoRef.current.currentTime = clickedTime;
      setCurrentTime(clickedTime);
    }
  };

  // Build dynamic Plotly traces based on active metrics and videos
  const generateTraces = () => {
    const traces = [];
    // Color palette to ensure videos look different
    const colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00C49F', '#FFBB28'];
    
    analysisResults.forEach((result, index) => {
      const baseColor = colors[index % colors.length];
      
      if (metrics.shannon) {
        traces.push({
          x: result.data.map(d => d.time), y: result.data.map(d => d.shannon),
          type: 'scatter', mode: 'lines', name: `${result.name} (Shannon)`,
          line: { color: baseColor, shape: 'spline' }
        });
      }
      if (metrics.renyi) {
        traces.push({
          x: result.data.map(d => d.time), y: result.data.map(d => d.renyi),
          type: 'scatter', mode: 'lines', name: `${result.name} (Rényi)`,
          line: { color: baseColor, dash: 'dash', shape: 'spline' }
        });
      }
      if (metrics.tsallis) {
        traces.push({
          x: result.data.map(d => d.time), y: result.data.map(d => d.tsallis),
          type: 'scatter', mode: 'lines', name: `${result.name} (Tsallis)`,
          line: { color: baseColor, dash: 'dot', shape: 'spline' }
        });
      }
    });
    return traces;
  };

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '20px', fontFamily: 'system-ui' }}>
      <h1>Multi-Video Entropy Analysis</h1>
      
      {/* Settings & Queue Panel */}
      <div style={{ display: 'flex', gap: '20px', marginBottom: '20px' }}>
        
        {/* Upload & List */}
        <div style={{ flex: '1', padding: '15px', backgroundColor: '#f5f5f5', borderRadius: '8px' }}>
          <h3>1. Queue Videos</h3>
          <input type="file" multiple accept="video/mp4,video/quicktime" onChange={handleAddFiles} />
          
          <ul style={{ listStyle: 'none', padding: 0, marginTop: '10px' }}>
            {videoQueue.map(video => (
              <li key={video.id} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px', padding: '5px', background: '#fff', borderRadius: '4px' }}>
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{video.name}</span>
                <button onClick={() => removeVideo(video.id)} style={{ color: 'red', border: 'none', background: 'none', cursor: 'pointer' }}>✖</button>
              </li>
            ))}
          </ul>
        </div>

        {/* Algorithm Toggles */}
        <div style={{ flex: '1', padding: '15px', backgroundColor: '#f5f5f5', borderRadius: '8px' }}>
          <h3>2. Select Algorithms</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <label><input type="checkbox" checked={metrics.shannon} onChange={() => toggleMetric('shannon')} /> Shannon Entropy</label>
            <label><input type="checkbox" checked={metrics.renyi} onChange={() => toggleMetric('renyi')} /> Rényi Entropy</label>
            <label><input type="checkbox" checked={metrics.tsallis} onChange={() => toggleMetric('tsallis')} /> Tsallis Entropy</label>
          </div>
        </div>

        {/* Action Button */}
        <div style={{ flex: '1', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <button 
            onClick={handleAnalyze} 
            disabled={videoQueue.length === 0 || isProcessing || (!metrics.shannon && !metrics.renyi && !metrics.tsallis)}
            style={{ padding: '15px 30px', fontSize: '18px', cursor: 'pointer', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '8px' }}
          >
            {isProcessing ? "Analyzing All Videos..." : "Run Analysis 🚀"}
          </button>
        </div>
      </div>

      {/* Visualizer Panel */}
      <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
        
        {/* Video Player */}
        <div style={{ flex: '1', minWidth: '400px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3>Video Preview</h3>
            {videoQueue.length > 0 && (
              <select 
                value={activeVideoIndex} 
                onChange={(e) => setActiveVideoIndex(Number(e.target.value))}
                style={{ padding: '5px' }}
              >
                {videoQueue.map((v, i) => (
                  <option key={v.id} value={i}>Preview: {v.name}</option>
                ))}
              </select>
            )}
          </div>
          
          {videoQueue.length > 0 ? (
            <video 
              ref={videoRef}
              src={videoQueue[activeVideoIndex]?.url}
              controls
              onTimeUpdate={handleTimeUpdate}
              style={{ width: '100%', borderRadius: '8px', backgroundColor: '#000' }}
            />
          ) : (
            <div style={{ width: '100%', height: '300px', backgroundColor: '#eaeaea', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '8px' }}>
              Add videos to begin
            </div>
          )}
        </div>

        {/* Master Graph */}
        <div style={{ flex: '2', minWidth: '600px', overflowX: 'auto' }}>
          <h3>Comparative Entropy Streams</h3>
          {analysisResults.length > 0 ? (
            <Plot
              data={generateTraces()}
              layout={{
                width: 900,
                height: 450,
                margin: { t: 20, r: 20, b: 40, l: 40 },
                xaxis: { title: 'Time (s)' },
                yaxis: { title: 'Information Bits / Units' },
                hovermode: 'x unified',
                shapes: [
                  { // Playback scrubber line
                    type: 'line', x0: currentTime, x1: currentTime,
                    y0: 0, y1: 1, yref: 'paper',
                    line: { color: 'red', width: 2, dash: 'dot' }
                  }
                ]
              }}
              onClick={handleChartClick}
            />
          ) : (
            <div style={{ width: '900px', height: '450px', backgroundColor: '#eaeaea', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '8px' }}>
              Awaiting Analysis...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}