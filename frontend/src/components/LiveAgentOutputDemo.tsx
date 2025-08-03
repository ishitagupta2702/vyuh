import React, { useState } from 'react';
import LiveAgentOutput from './LiveAgentOutput';
import './LiveAgentOutputDemo.css';

const LiveAgentOutputDemo: React.FC = () => {
  const [sessionId, setSessionId] = useState('test-correct-path');
  const [isStreaming, setIsStreaming] = useState(false);

  const handleStartStream = () => {
    if (sessionId.trim()) {
      setIsStreaming(true);
    }
  };

  const handleStopStream = () => {
    setIsStreaming(false);
  };

  return (
    <div className="live-agent-demo">
      <div className="demo-header">
        <h1>Live Agent Output Demo</h1>
        <p>Test real-time streaming of agent messages</p>
      </div>

      <div className="demo-controls">
        <div className="input-group">
          <label htmlFor="sessionId">Session ID:</label>
          <input
            type="text"
            id="sessionId"
            value={sessionId}
            onChange={(e) => setSessionId(e.target.value)}
            placeholder="Enter session ID (e.g., test-correct-path)"
          />
        </div>
        
        <div className="button-group">
          {!isStreaming ? (
            <button 
              onClick={handleStartStream}
              disabled={!sessionId.trim()}
              className="start-btn"
            >
              Start Stream
            </button>
          ) : (
            <button 
              onClick={handleStopStream}
              className="stop-btn"
            >
              Stop Stream
            </button>
          )}
        </div>
      </div>

      {isStreaming && (
        <div className="stream-container">
          <LiveAgentOutput sessionId={sessionId} />
        </div>
      )}

      <div className="demo-info">
        <h3>Available Test Sessions:</h3>
        <ul>
          <li><code>test-correct-path</code> - Recent test with JSON outputs</li>
          <li><code>c7f48bc8-96ed-40bb-be4e-71184ad3690d</code> - Original test session</li>
        </ul>
        <p>
          <strong>Note:</strong> Make sure the backend server is running on port 8000 
          and the session ID exists in the backend/runs directory.
        </p>
      </div>
    </div>
  );
};

export default LiveAgentOutputDemo;
