import React, { useState, useEffect, useRef } from 'react';

function App() {
  const [frame, setFrame] = useState(null);
  const [objects, setObjects] = useState([]);
  const [guidance, setGuidance] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [cameraEnabled, setCameraEnabled] = useState(false);
  const wsRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const lastSpokenRef = useRef('');
  const lastSpeakTimeRef = useRef(0);
  const frameIntervalRef = useRef(null);

  // Function to speak text
  const speak = (text) => {
    const now = Date.now();
    const timeSinceLastSpeak = now - lastSpeakTimeRef.current;
    
    // Only speak if text is new AND at least 2 seconds have passed since last speech
    if ('speechSynthesis' in window && text && 
        (text !== lastSpokenRef.current || timeSinceLastSpeak > 2000)) {
      // Cancel any ongoing speech
      window.speechSynthesis.cancel();
      
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.95;  // Slightly slower for clarity
      utterance.pitch = 1.0;
      utterance.volume = 1.0;
      
      window.speechSynthesis.speak(utterance);
      lastSpokenRef.current = text;
      lastSpeakTimeRef.current = now;
      
      console.log('🔊 Speaking:', text);
    }
  };

  // Start browser camera
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: 'environment' }
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
        setCameraEnabled(true);
        console.log('📹 Browser camera started');
      }
    } catch (err) {
      console.error('Camera access denied:', err);
      alert('Please allow camera access for real-time detection');
    }
  };

  // Send frames to backend
  const sendFrame = () => {
    if (!videoRef.current || !canvasRef.current || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    // Draw video frame to canvas
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);

    // Convert to base64 and send
    const frameData = canvas.toDataURL('image/jpeg', 0.7);
    
    try {
      wsRef.current.send(JSON.stringify({
        type: 'frame',
        frame: frameData
      }));
    } catch (err) {
      console.error('Error sending frame:', err);
    }
  };

  useEffect(() => {
    // Get WebSocket URL from environment or use localhost
    const wsUrl = process.env.REACT_APP_WS_URL 
      ? `wss://${process.env.REACT_APP_WS_URL.replace(/^https?:\/\//, '')}`
      : 'ws://localhost:8765';
    
    console.log('Connecting to WebSocket:', wsUrl);
    
    // Connect to backend WebSocket
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.frame) {
        setFrame(data.frame);
      }
      
      if (data.objects) {
        setObjects(data.objects);
        setIsThinking(false);
      }
      
      if (data.spoken_guidance) {
        setGuidance(data.spoken_guidance);
        speak(data.spoken_guidance); // Speak the guidance
      }

      if (data.thinking) {
        setIsThinking(true);
      }
    };

    ws.onerror = () => {
      console.log('WebSocket error - falling back to demo mode');
      startDemoMode();
    };

    ws.onopen = () => {
      console.log('WebSocket connected');
      // Start camera and frame sending
      startCamera();
      
      // Send frames at ~10 FPS
      frameIntervalRef.current = setInterval(sendFrame, 100);
    };

    return () => {
      ws.close();
      if (frameIntervalRef.current) {
        clearInterval(frameIntervalRef.current);
      }
      // Stop camera
      if (videoRef.current && videoRef.current.srcObject) {
        videoRef.current.srcObject.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  const startDemoMode = () => {
    // Demo data for when backend isn't running
    setTimeout(() => {
      setObjects([
        {
          label: 'person',
          distance: 'close',
          direction: 'ahead',
          motion: 'approaching',
          risk: 'medium',
          bbox: [0.3, 0.2, 0.6, 0.8]
        }
      ]);
      setGuidance('A person is approaching from ahead. Slow down.');
    }, 1000);
  };

  const getRiskColor = (risk) => {
    if (risk === 'imminent' || risk === 'high') return 'red';
    if (risk === 'medium') return 'yellow';
    return 'green';
  };

  const getRiskLabel = (risk) => {
    const labels = {
      'imminent': 'IMMINENT',
      'high': 'HIGH',
      'medium': 'MEDIUM',
      'low': 'LOW',
      'none': 'SAFE'
    };
    return labels[risk] || 'SAFE';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 p-6">
      {/* Hidden video and canvas for camera capture */}
      <video ref={videoRef} style={{ display: 'none' }} playsInline />
      <canvas ref={canvasRef} style={{ display: 'none' }} />
      
      {/* Header */}
      <header className="mb-8">
        <h1 className="text-4xl font-bold text-center bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
          Vision-to-Voice Assistant
        </h1>
        <p className="text-center text-gray-400 mt-2">
          AI-Powered Navigation for the Visually Impaired
        </p>
      </header>

      {/* Flow Indicator */}
      <div className="flex justify-center items-center gap-4 mb-8">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-blue-500"></div>
          <span className="text-sm text-gray-400">Detect</span>
        </div>
        <div className="w-8 h-0.5 bg-gray-700"></div>
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${isThinking ? 'bg-purple-500 pulse-thinking' : 'bg-gray-600'}`}></div>
          <span className="text-sm text-gray-400">Predict</span>
        </div>
        <div className="w-8 h-0.5 bg-gray-700"></div>
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${guidance ? 'bg-green-500' : 'bg-gray-600'}`}></div>
          <span className="text-sm text-gray-400">Warn</span>
        </div>
      </div>

      {/* Main Three-Panel Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 max-w-7xl mx-auto">
        
        {/* LEFT PANEL - Camera Feed */}
        <div className="lg:col-span-4">
          <div className="bg-gray-900/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-800 h-full">
            <h2 className="text-xl font-semibold mb-4 text-blue-400">Live Camera</h2>
            <div className="relative aspect-video bg-black rounded-lg overflow-hidden">
              {frame ? (
                <img src={`data:image/jpeg;base64,${frame}`} alt="Camera feed" className="w-full h-full object-cover" />
              ) : (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-gray-500">Connecting to camera...</p>
                  </div>
                </div>
              )}
              
              {/* Bounding boxes overlay */}
              {objects.map((obj, idx) => {
                if (!obj.bbox) return null;
                const [x1, y1, x2, y2] = obj.bbox;
                const color = getRiskColor(obj.risk);
                const colorClass = color === 'red' ? 'border-red-500' : color === 'yellow' ? 'border-yellow-500' : 'border-green-500';
                
                return (
                  <div
                    key={idx}
                    className={`absolute border-2 ${colorClass}`}
                    style={{
                      left: `${x1 * 100}%`,
                      top: `${y1 * 100}%`,
                      width: `${(x2 - x1) * 100}%`,
                      height: `${(y2 - y1) * 100}%`
                    }}
                  >
                    <div className={`absolute -top-6 left-0 px-2 py-1 rounded text-xs font-semibold ${
                      color === 'red' ? 'bg-red-500' : color === 'yellow' ? 'bg-yellow-500' : 'bg-green-500'
                    } text-white`}>
                      {obj.label.toUpperCase()}
                    </div>
                    
                    {/* Motion arrow */}
                    {obj.motion === 'approaching' && (
                      <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                        <div className="text-2xl animate-pulse">↓</div>
                      </div>
                    )}
                    {obj.motion === 'crossing' && (
                      <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                        <div className="text-2xl animate-pulse">→</div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
            
            <div className="mt-4 text-sm text-gray-500 text-center">
              Real-time object detection with motion tracking
            </div>
          </div>
        </div>

        {/* CENTER PANEL - AI Reasoning (MOST IMPORTANT) */}
        <div className="lg:col-span-4">
          <div className={`bg-gray-900/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-800 h-full transition-all ${
            isThinking ? 'glow-yellow' : ''
          }`}>
            <h2 className="text-xl font-semibold mb-4 text-purple-400">AI Reasoning</h2>
            
            {objects.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <p>Analyzing environment...</p>
              </div>
            ) : (
              <div className="space-y-4">
                {objects.map((obj, idx) => (
                  <div 
                    key={idx} 
                    className={`p-4 rounded-xl border-2 fade-in ${
                      obj.risk === 'imminent' || obj.risk === 'high' 
                        ? 'bg-red-950/30 border-red-500/50' 
                        : obj.risk === 'medium'
                        ? 'bg-yellow-950/30 border-yellow-500/50'
                        : 'bg-green-950/30 border-green-500/50'
                    }`}
                  >
                    <div className="space-y-3">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="text-sm text-gray-400">Detected Object</p>
                          <p className="text-lg font-semibold capitalize">{obj.label}</p>
                        </div>
                        <div className={`px-3 py-1 rounded-full text-xs font-bold ${
                          obj.risk === 'imminent' || obj.risk === 'high'
                            ? 'bg-red-500'
                            : obj.risk === 'medium'
                            ? 'bg-yellow-500'
                            : 'bg-green-500'
                        }`}>
                          {getRiskLabel(obj.risk)}
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <p className="text-gray-400">Distance</p>
                          <p className="font-medium capitalize">{obj.distance.replace('_', ' ')}</p>
                        </div>
                        <div>
                          <p className="text-gray-400">Direction</p>
                          <p className="font-medium capitalize">{obj.direction}</p>
                        </div>
                      </div>

                      {obj.motion && obj.motion !== 'stationary' && (
                        <div>
                          <p className="text-gray-400 text-sm">Motion Pattern</p>
                          <p className="font-medium capitalize">{obj.motion}</p>
                        </div>
                      )}

                      <div className="pt-2 border-t border-gray-700">
                        <p className="text-gray-400 text-sm">AI Decision</p>
                        <p className="font-medium">
                          {obj.risk === 'imminent' || obj.risk === 'high'
                            ? '⚠️ Warn user to stop immediately'
                            : obj.risk === 'medium'
                            ? '⚡ Alert user to slow down'
                            : '✓ Monitor and proceed safely'}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* RIGHT PANEL - Spoken Guidance */}
        <div className="lg:col-span-4">
          <div className={`bg-gray-900/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-800 h-full transition-all ${
            guidance ? 'glow-green' : ''
          }`}>
            <h2 className="text-xl font-semibold mb-4 text-green-400">Spoken Guidance</h2>
            
            {guidance ? (
              <div className="fade-in">
                <div className="bg-gradient-to-br from-green-900/30 to-blue-900/30 rounded-xl p-6 border border-green-500/30">
                  <div className="flex items-start gap-3 mb-4">
                    <div className="text-3xl">🔊</div>
                    <div className="flex-1">
                      <p className="text-lg leading-relaxed">{guidance}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-400">
                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                    <span>Speaking now...</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <div className="text-4xl mb-3">🎧</div>
                <p>Waiting for guidance...</p>
              </div>
            )}

            <div className="mt-6 p-4 bg-gray-800/50 rounded-lg">
              <p className="text-sm text-gray-400">
                <span className="font-semibold text-green-400">ElevenLabs TTS</span> provides natural voice output to guide users safely through their environment.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Footer Tech Stack */}
      <footer className="mt-8 text-center">
        <div className="inline-flex items-center gap-4 text-sm text-gray-500">
          <span>YOLO11 Detection</span>
          <span>•</span>
          <span>MiDaS Depth</span>
          <span>•</span>
          <span>ANI Motion Tracking</span>
          <span>•</span>
          <span>Gemini AI</span>
          <span>•</span>
          <span>ElevenLabs TTS</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
