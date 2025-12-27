import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { api } from '../config/api';

// Typewriter hook for streaming effect
function useTypewriter(text, speed = 15) {
    const [displayedText, setDisplayedText] = useState('');
    const [isComplete, setIsComplete] = useState(false);

    useEffect(() => {
        if (!text) return;

        setDisplayedText('');
        setIsComplete(false);

        let i = 0;
        const interval = setInterval(() => {
            if (i < text.length) {
                setDisplayedText(text.slice(0, i + 1));
                i++;
            } else {
                setIsComplete(true);
                clearInterval(interval);
            }
        }, speed);

        return () => clearInterval(interval);
    }, [text, speed]);

    return { displayedText, isComplete };
}

// Message component with typewriter
function Message({ message, isLatest }) {
    const { displayedText, isComplete } = useTypewriter(
        isLatest && message.role === 'assistant' ? message.content : null,
        12
    );

    const content = isLatest && message.role === 'assistant' && !isComplete
        ? displayedText
        : message.content;

    return (
        <div className={`chat-message ${message.role}`}>
            {message.role === 'assistant' && (
                <div className="message-avatar">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                        <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" strokeWidth="2" />
                        <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="2" />
                        <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2" />
                    </svg>
                </div>
            )}
            <div className="message-content">
                {message.role === 'assistant' ? (
                    <ReactMarkdown
                        components={{
                            code: ({ inline, className, children }) => {
                                if (inline) {
                                    return <code className="inline-code">{children}</code>;
                                }
                                return (
                                    <pre className="code-block">
                                        <code>{children}</code>
                                    </pre>
                                );
                            }
                        }}
                    >
                        {content}
                    </ReactMarkdown>
                ) : (
                    <p>{content}</p>
                )}

                {message.sources && message.sources.length > 0 && isComplete && (
                    <div className="message-sources">
                        <span className="sources-label">Sources:</span>
                        {message.sources.slice(0, 4).map((src, j) => (
                            <span key={j} className="source-pill" title={src.preview || ''}>
                                {src.section || src.type}
                                {src.line && <span className="source-line">:{src.line}</span>}
                            </span>
                        ))}
                    </div>
                )}

                {message.context && (
                    <div className="message-context">
                        <span className="context-path">Context: {message.context}</span>
                    </div>
                )}
            </div>
        </div>
    );
}

function ResultsPage({ repo, results, onBack }) {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);

    useEffect(() => {
        // Add initial AI summary
        if (results.suggestions?.summary) {
            setMessages([{
                role: 'assistant',
                content: `**Repository Analysis Complete**\n\n${results.suggestions.summary}`,
                context: 'README.md'
            }]);
        }
    }, []);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSubmit = async (question) => {
        if (!question.trim() || loading) return;

        setMessages(prev => [...prev, { role: 'user', content: question }]);
        setInput('');
        setLoading(true);

        try {
            const res = await fetch(api.analyze(), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ repo_name: repo, question })
            });

            const data = await res.json();

            setMessages(prev => [...prev, {
                role: 'assistant',
                content: data.answer || 'Unable to answer that question.',
                sources: data.sources,
                context: data.sources?.[0]?.section || 'Repository'
            }]);
        } catch (err) {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Sorry, something went wrong. Please try again.'
            }]);
        } finally {
            setLoading(false);
        }
    };

    const quickQuestions = [
        "How do I get started?",
        "What's the architecture?",
        "Best first contribution?",
        "How to run tests?"
    ];

    // Extract tech info
    const languages = results.techStack?.languages || [];
    const frameworks = results.techStack?.frameworks || [];
    const warmthScore = results.warmth?.score || 0;
    const warmthLabel = results.warmth?.label || 'Unknown';

    return (
        <div className="results-page-v2">
            {/* Sidebar */}
            <aside className="results-sidebar">
                <button className="sidebar-back" onClick={onBack}>
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <path d="M10 12L6 8L10 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                    </svg>
                    Back
                </button>

                {/* Mission Brief */}
                <div className="mission-brief">
                    <p>{results.suggestions?.summary?.split('.')[0] || repo.split('/')[1]}.</p>
                </div>

                <div className="sidebar-section">
                    <h3>Repository</h3>
                    <div className="repo-info">
                        <a href={`https://github.com/${repo}`} target="_blank" rel="noopener noreferrer" className="repo-link">
                            {repo}
                            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                                <path d="M3.5 8.5L8.5 3.5M8.5 3.5H4.5M8.5 3.5V7.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                            </svg>
                        </a>
                    </div>
                </div>

                {/* Warmth Visualization */}
                <div className="sidebar-section">
                    <h3>Maintainer Warmth</h3>
                    <div className="warmth-visual">
                        <div className="warmth-bar">
                            <div
                                className="warmth-fill"
                                style={{ width: `${warmthScore}%` }}
                            />
                        </div>
                        <div className="warmth-info">
                            <span className="warmth-score">{warmthScore}/100</span>
                            <span className={`warmth-label ${warmthScore > 70 ? 'warm' : warmthScore > 40 ? 'neutral' : 'cold'}`}>
                                {warmthLabel}
                            </span>
                        </div>
                    </div>
                </div>

                {/* Tech Stack */}
                {(languages.length > 0 || frameworks.length > 0) && (
                    <div className="sidebar-section">
                        <h3>Tech Stack</h3>
                        <div className="tech-list">
                            {languages.map((lang, i) => (
                                <span key={i} className="tech-item lang">{lang}</span>
                            ))}
                            {frameworks.map((fw, i) => (
                                <span key={i} className="tech-item framework">{fw}</span>
                            ))}
                        </div>
                    </div>
                )}

                {/* Contribution Ideas */}
                {results.suggestions && (
                    <div className="sidebar-section">
                        <h3>Where to Start</h3>
                        <div className="ideas-list">
                            {results.suggestions.beginner_friendly?.slice(0, 3).map((idea, i) => (
                                <div key={i} className="idea-item">
                                    <span className="idea-badge">Easy</span>
                                    <span className="idea-text">{idea}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Setup Commands */}
                {results.setup?.commands?.length > 0 && (
                    <div className="sidebar-section">
                        <h3>Quick Setup</h3>
                        <div className="setup-commands">
                            {results.setup.commands.slice(0, 3).map((cmd, i) => (
                                <code key={i} className="cmd">{cmd}</code>
                            ))}
                        </div>
                    </div>
                )}
            </aside>

            {/* Main Chat Area */}
            <main className="results-main">
                <div className="chat-messages">
                    {messages.length === 0 && (
                        <div className="chat-welcome">
                            <h1>Ask about {repo.split('/')[1]}</h1>
                            <p>I've analyzed the repository structure, README, and open issues. Ask me anything.</p>

                            <div className="quick-prompts">
                                {quickQuestions.map((q, i) => (
                                    <button
                                        key={i}
                                        className="quick-prompt"
                                        onClick={() => handleSubmit(q)}
                                    >
                                        {q}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {messages.map((msg, i) => (
                        <Message
                            key={i}
                            message={msg}
                            isLatest={i === messages.length - 1 && !loading}
                        />
                    ))}

                    {loading && (
                        <div className="chat-message assistant">
                            <div className="message-avatar">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                                    <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" strokeWidth="2" />
                                    <path d="M2 17L12 22L22 17" stroke="currentColor" strokeWidth="2" />
                                    <path d="M2 12L12 17L22 12" stroke="currentColor" strokeWidth="2" />
                                </svg>
                            </div>
                            <div className="message-content">
                                <div className="typing-indicator">
                                    <span></span><span></span><span></span>
                                </div>
                            </div>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>

                {/* Input */}
                <div className="chat-input-container">
                    <form onSubmit={(e) => { e.preventDefault(); handleSubmit(input); }} className="chat-form">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Ask anything about this repository..."
                            disabled={loading}
                            className="chat-input"
                        />
                        <button type="submit" disabled={loading || !input.trim()} className="chat-submit">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                                <path d="M22 2L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                                <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                        </button>
                    </form>
                </div>
            </main>
        </div>
    );
}

export default ResultsPage;
