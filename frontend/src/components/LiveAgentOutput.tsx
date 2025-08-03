import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import './LiveAgentOutput.css';

interface AgentMessage {
  agent: string;
  content: string;
  type: string;
}

interface LiveAgentOutputProps {
  sessionId: string;
}

const LiveAgentOutput: React.FC<LiveAgentOutputProps> = ({ sessionId }) => {
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (!sessionId) return;

    // Close existing connection if any
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    // Create new EventSource connection
    const eventSource = new EventSource(`/api/stream/${sessionId}`);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setIsConnected(true);
      setError(null);
      console.log('SSE connection opened');
    };

    eventSource.onmessage = (event) => {
      const data = event.data;
      
      // Check if this is a JSON message
      if (data.startsWith('{')) {
        try {
          const agentMessage: AgentMessage = JSON.parse(data);
          setMessages(prev => [...prev, agentMessage]);
          console.log('Received agent message:', agentMessage);
        } catch (err) {
          console.error('Failed to parse JSON message:', err);
        }
      } else if (data.includes('[COMPLETE]')) {
        console.log('Stream completed');
        eventSource.close();
        setIsConnected(false);
      } else if (data.includes('[ERROR]')) {
        setError(data);
        console.error('Stream error:', data);
        eventSource.close();
        setIsConnected(false);
      }
    };

    eventSource.onerror = (event) => {
      console.error('SSE connection error:', event);
      setError('Connection error occurred');
      setIsConnected(false);
      eventSource.close();
    };

    // Cleanup function
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [sessionId]);

  const getAgentAvatar = (agentName: string) => {
    const avatars: { [key: string]: string } = {
      'researcher': '🔍',
      'writer': '✍️',
      'system': '🤖',
      'default': '👤'
    };
    return avatars[agentName] || avatars.default;
  };

  const getAgentDisplayName = (agentName: string) => {
    const names: { [key: string]: string } = {
      'researcher': 'Researcher',
      'writer': 'Writer',
      'system': 'System',
      'default': agentName
    };
    return names[agentName] || names.default;
  };

  return (
    <div className="live-agent-output">
      {/* Connection Status */}
      <div className="connection-status">
        {isConnected ? (
          <span className="status-connected">🟢 Connected - Streaming live</span>
        ) : error ? (
          <span className="status-error">🔴 Error: {error}</span>
        ) : (
          <span className="status-connecting">🟡 Connecting...</span>
        )}
      </div>

      {/* Messages Container */}
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="no-messages">
            <p>Waiting for agent messages...</p>
          </div>
        ) : (
          messages.map((message, index) => (
            <div key={index} className={`message ${message.agent}`}>
              <div className="message-header">
                <span className="agent-avatar">
                  {getAgentAvatar(message.agent)}
                </span>
                <span className="agent-name">
                  {getAgentDisplayName(message.agent)}
                </span>
                {message.type === 'final' && (
                  <span className="message-type">Final Output</span>
                )}
              </div>
              <div className="message-content">
                <ReactMarkdown>{message.content}</ReactMarkdown>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default LiveAgentOutput;
