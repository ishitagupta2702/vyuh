import React, { useState, useEffect } from 'react';
import AgentCard from './AgentCard';
import CrewCart from './CrewCart';
import './CrewBuilder.css';

const CrewBuilder = () => {
  const [agents, setAgents] = useState({});
  const [crew, setCrew] = useState([]);
  const [topic, setTopic] = useState("");
  const [loading, setLoading] = useState(true);
  const [launchLoading, setLaunchLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [result, setResult] = useState(null);
  const [pollingResult, setPollingResult] = useState(false);

  useEffect(() => {
    fetchAgents();
  }, []);

  // Poll for results when we have a sessionId
  useEffect(() => {
    if (!sessionId || !pollingResult) return;

    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/api/result/${sessionId}`);
        
        if (response.ok) {
          const data = await response.json();
          setResult(data.content);
          setPollingResult(false);
          clearInterval(pollInterval);
        } else if (response.status === 404) {
          // Result not ready yet, continue polling
          console.log('Result not ready yet, continuing to poll...');
        } else {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
      } catch (err) {
        console.error('Error polling for result:', err);
        setPollingResult(false);
        clearInterval(pollInterval);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(pollInterval);
  }, [sessionId, pollingResult]);

  const fetchAgents = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/agents');
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setAgents(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch agents');
      console.error('Error fetching agents:', err);
    } finally {
      setLoading(false);
    }
  };

  const addToCrew = (agentId) => {
    if (!crew.includes(agentId)) {
      setCrew([...crew, agentId]);
    }
  };

  const removeFromCrew = (agentId) => {
    setCrew(crew.filter(id => id !== agentId));
  };

  const handleLaunchCrew = async () => {
    if (crew.length === 0) {
      alert('Please select at least one agent');
      return;
    }
    
    if (!topic.trim()) {
      alert('Please enter a topic');
      return;
    }

    try {
      setLaunchLoading(true);
      const payload = {
        crew: crew,
        topic: topic.trim()
      };
      
      const response = await fetch('/api/launch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setSessionId(data.session_id);
      setPollingResult(true);
      setResult(null); // Clear any previous result
    } catch (err) {
      alert(`Error launching crew: ${err instanceof Error ? err.message : 'Failed to launch crew'}`);
    } finally {
      setLaunchLoading(false);
    }
  };

  const formatAgentName = (id) => {
    return id.charAt(0).toUpperCase() + id.slice(1);
  };

  const handleReset = () => {
    setCrew([]);
    setTopic("");
    setSessionId(null);
    setResult(null);
    setPollingResult(false);
  };

  if (loading) {
    return (
      <div className="crew-builder">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading available agents...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="crew-builder">
        <div className="error-container">
          <h3>Error Loading Agents</h3>
          <p>{error}</p>
          <button onClick={fetchAgents} className="retry-btn">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="crew-builder">
      <div className="crew-builder-header">
        <h2>Available Agents</h2>
        <p>Select agents to add to your crew</p>
      </div>
      
      <div className="topic-input-section">
        <label htmlFor="topic-input" className="topic-label">Your Idea</label>
        <textarea
          id="topic-input"
          className="topic-input"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Enter your topic or idea..."
          rows={3}
        />
      </div>
      
      <div className="crew-builder-content">
        <div className="agents-section">
          <div className="agents-grid">
            {Object.entries(agents).map(([id, agent]) => (
              <AgentCard
                key={id}
                id={id}
                name={formatAgentName(id)}
                role={agent.role}
                goal={agent.goal}
                onAdd={addToCrew}
              />
            ))}
          </div>
        </div>
        
        <div className="crew-section">
          <CrewCart
            crew={crew}
            onRemove={removeFromCrew}
            onLaunch={handleLaunchCrew}
            launchLoading={launchLoading}
            topic={topic}
          />
        </div>
      </div>

      {/* Result Display Section */}
      {(pollingResult || result) && (
        <div className="result-section">
          <div className="result-header">
            <h3>Crew Execution Result</h3>
            {sessionId && <span className="session-id">Session: {sessionId}</span>}
          </div>
          
          {pollingResult && !result && (
            <div className="result-loading">
              <div className="loading-spinner"></div>
              <p>Executing crew... This may take a few moments.</p>
            </div>
          )}
          
          {result && (
            <div className="result-content">
              <textarea
                className="result-textarea"
                value={result}
                readOnly
                rows={10}
                placeholder="Crew execution result will appear here..."
              />
              <div className="result-actions">
                <button onClick={handleReset} className="reset-btn">
                  Start Over
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default CrewBuilder;
