import { useState } from 'react';
import { sendChatMessage } from '../api/client';
import type { GenerationTask } from '../types';

interface ChatInterfaceProps {
  task: GenerationTask | null;
}

interface Message {
  id: string;
  sender: 'user' | 'agent';
  text: string;
}

export function ChatInterface({ task }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    { id: 'initial', sender: 'agent', text: 'Hello! I am DocuForge. Upload your files and click Generate to begin. You can send me additional instructions here.' }
  ]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);

  const handleSend = async () => {
    if (!input.trim() || !task?.taskId) return;
    
    const userMsg: Message = { id: Date.now().toString(), sender: 'user', text: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsSending(true);

    try {
      const response = await sendChatMessage({
        task_id: task.taskId,
        message: userMsg.text,
      });

      setMessages((prev) => [
        ...prev,
        { id: (Date.now() + 1).toString(), sender: 'agent', text: response.message }
      ]);
    } catch (err) {
      console.error('Chat error', err);
      setMessages((prev) => [
        ...prev,
        { id: (Date.now() + 1).toString(), sender: 'agent', text: 'Sorry, there was an error sending your message.' }
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', height: '100%', maxHeight: '400px' }}>
      <div style={{ padding: '1rem', borderBottom: '1px solid var(--border)', backgroundColor: 'var(--bg-tertiary)' }}>
        <h3 style={{ fontSize: '1rem', margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span>💬</span> Chat with DocuForge
        </h3>
      </div>
      
      <div style={{ flex: 1, overflowY: 'auto', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {messages.map((msg) => (
          <div 
            key={msg.id} 
            style={{ 
              display: 'flex', 
              justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start' 
            }}
          >
            <div 
              style={{ 
                maxWidth: '85%', 
                padding: '0.75rem 1rem', 
                borderRadius: 'var(--radius-lg)',
                backgroundColor: msg.sender === 'user' ? 'var(--accent)' : 'var(--bg-tertiary)',
                color: msg.sender === 'user' ? '#fff' : 'var(--text-primary)',
                border: msg.sender === 'user' ? 'none' : '1px solid var(--border)',
                borderBottomRightRadius: msg.sender === 'user' ? '4px' : 'var(--radius-lg)',
                borderBottomLeftRadius: msg.sender === 'agent' ? '4px' : 'var(--radius-lg)',
                fontSize: '0.9rem',
              }}
            >
              {msg.text}
            </div>
          </div>
        ))}
        {isSending && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div style={{ 
                padding: '0.75rem 1rem', 
                borderRadius: 'var(--radius-lg)',
                backgroundColor: 'var(--bg-tertiary)',
                border: '1px solid var(--border)',
                borderBottomLeftRadius: '4px',
              }}
            >
              <div className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px', borderTopColor: 'var(--text-secondary)' }}></div>
            </div>
          </div>
        )}
      </div>

      <div style={{ padding: '1rem', borderTop: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <input
            className="input"
            type="text"
            placeholder={task ? "Type instructions..." : "Start generation first..."}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={!task || isSending}
            style={{ flex: 1 }}
          />
          <button 
            className="btn btn-primary btn-icon" 
            onClick={handleSend}
            disabled={!task || !input.trim() || isSending}
          >
            ↗
          </button>
        </div>
      </div>
    </div>
  );
}
