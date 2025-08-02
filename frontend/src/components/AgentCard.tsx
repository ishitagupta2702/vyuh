import React from 'react';
import './AgentCard.css';

interface AgentCardProps {
  id: string;
  name: string;
  role: string;
  goal: string;
  onAdd: (id: string) => void;
  isSelected?: boolean;
}

const AgentCard: React.FC<AgentCardProps> = ({ id, name, role, goal, onAdd, isSelected = false }) => {
  return (
    <div className={`agent-card ${isSelected ? 'selected' : ''}`}>
              <div className="agent-card-header">
          <h3 className="agent-name">{name}</h3>
          <span className="agent-id">#{id}</span>
          {isSelected && <span className="selected-badge">✓</span>}
        </div>
      
      <div className="agent-card-content">
        <div className="agent-section">
          <h4 className="section-title">Role</h4>
          <p className="section-content">{role}</p>
        </div>
        
        <div className="agent-section">
          <h4 className="section-title">Goal</h4>
          <p className="section-content">{goal}</p>
        </div>
      </div>
      
      <div className="agent-card-footer">
        <button 
          className={`add-to-crew-btn ${isSelected ? 'selected' : ''}`}
          onClick={() => onAdd(id)}
        >
          {isSelected ? 'Remove from Crew' : 'Add to Crew'}
        </button>
      </div>
    </div>
  );
};

export default AgentCard;
