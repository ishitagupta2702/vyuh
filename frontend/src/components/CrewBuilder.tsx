import React, { useState, useEffect } from 'react';
import AgentCard from './AgentCard';
import './CrewBuilder.css';

interface Agent {
  role: string;
  goal: string;
  backstory: string;
}

interface AgentsData {
  [key: string]: Agent;
}

interface LaunchResponse {
  session_id: string;
  status: string;
  result?: string;
}

const CrewBuilder: React.FC = () => {
  const [agents, setAgents] = useState<AgentsData>({});
  const [selectedCrew, setSelectedCrew] = useState<string[]>([]);
  const [topic, setTopic] = useState("");
  const [loading, setLoading] = useState(true);
  const [launchLoading, setLaunchLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAgents();
  }, []);

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

  const handleAddToCrew = (agentId: string) => {
    setSelectedCrew(prev => 
      prev.includes(agentId) 
        ? prev.filter(id => id !== agentId) 
        : [...prev, agentId]
    );
  };

  const onLaunch = async () => {
    if (selectedCrew.length === 0) {
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
        crew: selectedCrew,
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

      const data: LaunchResponse = await response.json();
      alert(`Crew launched successfully!\nSession ID: ${data.session_id}`);
    } catch (err) {
      alert(`Error launching crew: ${err instanceof Error ? err.message : 'Failed to launch crew'}`);
    } finally {
      setLaunchLoading(false);
    }
  };

  const formatAgentName = (id: string): string => {
    return id.charAt(0).toUpperCase() + id.slice(1);
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
      
      <div className="agents-grid">
        {Object.entries(agents).map(([id, agent]) => (
          <AgentCard
            key={id}
            id={id}
            name={formatAgentName(id)}
            role={agent.role}
            goal={agent.goal}
            onAdd={handleAddToCrew}
            isSelected={selectedCrew.includes(id)}
          />
        ))}
      </div>

      {selectedCrew.length > 0 && (
        <div className="crew-launch-section">
          <h3>Selected Crew ({selectedCrew.length} agents)</h3>
          <div className="selected-crew">
            {selectedCrew.map(agentId => (
              <span key={agentId} className="crew-member">
                {formatAgentName(agentId)}
              </span>
            ))}
          </div>
          <button 
            onClick={onLaunch} 
            disabled={launchLoading || !topic.trim()} 
            className="launch-btn"
          >
            {launchLoading ? 'Launching...' : 'Launch Crew'}
          </button>
        </div>
      )}
    </div>
  );
};

export default CrewBuilder;
