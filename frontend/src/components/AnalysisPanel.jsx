import { useState } from 'react';

function AnalysisPanel({ onAnalyze, analysis, loading }) {
    const [question, setQuestion] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (question.trim()) onAnalyze(question.trim());
    };

    const quickQuestions = [
        "What is this project?",
        "Tech stack used?",
        "How to contribute?"
    ];

    return (
        <div className="panel">
            <h2>Ask about this repository</h2>

            <div className="quick-questions">
                {quickQuestions.map((q, i) => (
                    <button
                        key={i}
                        className="quick-btn"
                        onClick={() => { setQuestion(q); onAnalyze(q); }}
                        disabled={loading}
                    >
                        {q}
                    </button>
                ))}
            </div>

            <form onSubmit={handleSubmit} className="question-form">
                <input
                    type="text"
                    className="question-input"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="Ask anything..."
                    disabled={loading}
                />
                <button type="submit" className="btn btn-primary" disabled={loading || !question.trim()}>
                    {loading ? '...' : 'Ask'}
                </button>
            </form>

            {analysis && (
                <div className="answer-box">
                    <div className="label">Response</div>
                    <div className="text">{analysis.answer}</div>

                    {analysis.sources && analysis.sources.length > 0 && (
                        <div className="sources">
                            <div className="sources-label">Sources</div>
                            {analysis.sources.map((source, i) => (
                                <span key={i} className="source-tag">
                                    <span className="type">{source.type}</span>
                                    <span className="score">{(source.score * 100).toFixed(0)}%</span>
                                </span>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default AnalysisPanel;
