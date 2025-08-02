import React from 'react';
import './CrewCart.css';

const CrewCart = ({ crew, onRemove, onLaunch, launchLoading = false, topic = "" }) => {
  const formatAgentName = (id) => {
    return id.charAt(0).toUpperCase() + id.slice(1);
  };

  if (crew.length === 0) {
    return (
      <div className="crew-cart">
        <div className="crew-cart-header">
          <h3>Selected Crew</h3>
        </div>
        <div className="crew-cart-empty">
          <p>No agents selected</p>
          <span>Add agents to your crew to get started</span>
        </div>
      </div>
    );
  }

  return (
    <div className="crew-cart">
      <div className="crew-cart-header">
        <h3>Selected Crew</h3>
        <span className="crew-count">{crew.length} agent{crew.length !== 1 ? 's' : ''}</span>
      </div>
      
      <div className="crew-list">
        {crew.map((agentId) => (
          <div key={agentId} className="crew-item">
            <div className="crew-item-info">
              <span className="crew-agent-id">#{agentId}</span>
              <span className="crew-agent-name">{formatAgentName(agentId)}</span>
            </div>
            <button 
              className="remove-btn"
              onClick={() => onRemove(agentId)}
              title="Remove from crew"
            >
              ×
            </button>
          </div>
        ))}
      </div>
      
      <div className="crew-cart-footer">
        <button 
          className="launch-crew-btn"
          onClick={onLaunch}
          disabled={crew.length === 0 || !topic.trim() || launchLoading}
        >
          {launchLoading ? 'Launching...' : 'Launch Crew'}
        </button>
      </div>
    </div>
  );
};

export default CrewCart;
