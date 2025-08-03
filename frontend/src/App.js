import React, { useState } from 'react';
import './App.css';
import CrewBuilder from './components/CrewBuilder.js';
import LiveAgentOutputDemo from './components/LiveAgentOutputDemo.js';

function App() {
  const [currentView, setCurrentView] = useState('crew-builder');

  return (
    <div className="App">
      <header className="App-header">
        <h1>Vyuh Crew Builder</h1>
        <p>Build and launch collaborative AI agent crews</p>
        <nav className="nav-tabs">
          <button 
            className={currentView === 'crew-builder' ? 'active' : ''}
            onClick={() => setCurrentView('crew-builder')}
          >
            Crew Builder
          </button>
          <button 
            className={currentView === 'live-output' ? 'active' : ''}
            onClick={() => setCurrentView('live-output')}
          >
            Live Output Demo
          </button>
        </nav>
      </header>
      <main>
        {currentView === 'crew-builder' ? (
          <CrewBuilder />
        ) : (
          <LiveAgentOutputDemo />
        )}
      </main>
    </div>
  );
}

export default App;
