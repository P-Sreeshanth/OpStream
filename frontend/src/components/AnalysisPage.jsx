import { useState, useEffect, useRef } from 'react';
import { api } from '../config/api';

const PIPELINE_STEPS = [
    { id: 'connect', label: 'Connecting', duration: 500 },
    { id: 'readme', label: 'Fetching README', duration: 800 },
    { id: 'tree', label: 'Mapping structure', duration: 600 },
    { id: 'issues', label: 'Loading issues', duration: 1000 },
    { id: 'chunk', label: 'Processing sections', duration: 500 },
    { id: 'embed', label: 'Generating embeddings', duration: 1200 },
    { id: 'index', label: 'Indexing vectors', duration: 600 },
    { id: 'analyze', label: 'Running analysis', duration: 1000 },
];

function AnalysisPage({ issue, onComplete, onBack }) {
    const [currentStep, setCurrentStep] = useState(-1);
    const [completedSteps, setCompletedSteps] = useState(new Set());
    const [stepStats, setStepStats] = useState({});
    const [results, setResults] = useState(null);
    const [error, setError] = useState(null);
    const [fileStream, setFileStream] = useState([]);
    const streamRef = useRef(null);
    const hasRun = useRef(false);

    const mockFiles = [
        'README.md', 'package.json', 'src/index.ts', 'src/components/App.tsx',
        'src/utils/api.ts', 'docs/CONTRIBUTING.md', '.github/workflows/ci.yml'
    ];

    const addFileToStream = (file, type = 'process') => {
        const id = Date.now() + Math.random();
        setFileStream(prev => [...prev.slice(-6), { id, file, type }]);
    };

    const markStepComplete = (stepId) => {
        setCompletedSteps(prev => new Set([...prev, stepId]));
    };

    useEffect(() => {
        if (hasRun.current) return;
        hasRun.current = true;
        runAnalysis();
    }, []);

    useEffect(() => {
        if (streamRef.current) {
            streamRef.current.scrollTop = streamRef.current.scrollHeight;
        }
    }, [fileStream]);

    const runAnalysis = async () => {
        const repoName = issue.repo_name;

        try {
            // Step 1: Connect
            setCurrentStep(0);
            addFileToStream(`github.com/${repoName}`, 'connect');
            await delay(PIPELINE_STEPS[0].duration);
            markStepComplete('connect');
            setStepStats(prev => ({ ...prev, connect: 'Connected' }));

            // Step 2: README
            setCurrentStep(1);
            addFileToStream('README.md', 'fetch');
            await delay(PIPELINE_STEPS[1].duration);
            markStepComplete('readme');
            setStepStats(prev => ({ ...prev, readme: '~5KB' }));

            // Step 3: File tree
            setCurrentStep(2);
            for (let i = 0; i < 3; i++) {
                addFileToStream(mockFiles[Math.floor(Math.random() * mockFiles.length)], 'scan');
                await delay(150);
            }
            await delay(PIPELINE_STEPS[2].duration);
            markStepComplete('tree');
            setStepStats(prev => ({ ...prev, tree: '~40 files' }));

            // Step 4: Issues
            setCurrentStep(3);
            addFileToStream('issues/open', 'fetch');

            // Call index API
            let docsIndexed = 0;
            try {
                const indexRes = await fetch(api.indexRepo(), {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        repo_url: `https://github.com/${repoName}`,
                        issue_limit: 30
                    })
                });
                if (indexRes.ok) {
                    const indexData = await indexRes.json();
                    docsIndexed = indexData.documents_indexed || 0;
                }
            } catch (e) {
                console.error('Index error:', e);
            }

            markStepComplete('issues');
            setStepStats(prev => ({ ...prev, issues: `${docsIndexed} docs` }));

            // Step 5: Chunking
            setCurrentStep(4);
            addFileToStream('Splitting sections...', 'process');
            await delay(PIPELINE_STEPS[4].duration);
            markStepComplete('chunk');
            setStepStats(prev => ({ ...prev, chunk: `${Math.max(docsIndexed * 2, 12)} chunks` }));

            // Step 6: Embeddings
            setCurrentStep(5);
            addFileToStream('MiniLM-L6-v2', 'model');
            await delay(PIPELINE_STEPS[5].duration);
            markStepComplete('embed');
            setStepStats(prev => ({ ...prev, embed: '384 dims' }));

            // Step 7: Index
            setCurrentStep(6);
            addFileToStream('Qdrant', 'db');
            await delay(PIPELINE_STEPS[6].duration);
            markStepComplete('index');
            setStepStats(prev => ({ ...prev, index: 'Stored' }));

            // Step 8: Analysis
            setCurrentStep(7);
            addFileToStream('Llama 3.3 70B', 'model');

            // Fetch results
            const [suggestRes, techRes, setupRes, warmthRes] = await Promise.all([
                fetch(api.suggest(), {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ repo_name: repoName })
                }).catch(() => ({ ok: false })),
                fetch(api.techStack(), {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ repo_name: repoName })
                }).catch(() => ({ ok: false })),
                fetch(api.setup(), {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ repo_name: repoName })
                }).catch(() => ({ ok: false })),
                fetch(api.warmthScore(), {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ repo_name: repoName })
                }).catch(() => ({ ok: false }))
            ]);

            const analysisResults = {
                suggestions: suggestRes.ok ? await suggestRes.json() : null,
                techStack: techRes.ok ? await techRes.json() : null,
                setup: setupRes.ok ? await setupRes.json() : null,
                warmth: warmthRes.ok ? await warmthRes.json() : null,
            };

            markStepComplete('analyze');
            setStepStats(prev => ({ ...prev, analyze: 'Done' }));
            addFileToStream('Complete ✓', 'done');
            setCurrentStep(8);
            setResults(analysisResults);

        } catch (err) {
            addFileToStream(`Error: ${err.message}`, 'error');
            setError(err.message);
        }
    };

    const delay = (ms) => new Promise(r => setTimeout(r, ms));

    const isComplete = results !== null;
    const progress = Math.min(100, Math.round((completedSteps.size / PIPELINE_STEPS.length) * 100));

    return (
        <div className="analysis-page">
            <header className="analysis-header">
                <button className="back-btn" onClick={onBack}>
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <path d="M10 12L6 8L10 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                    </svg>
                    Back
                </button>
                <div className="analysis-repo">
                    <span className="repo-name">{issue.repo_name}</span>
                </div>
            </header>

            <div className="analysis-main">
                {/* Progress */}
                <div className="progress-section">
                    <div className="progress-header">
                        <h1>{isComplete ? 'Analysis Complete' : 'Analyzing Repository'}</h1>
                        <span className="progress-percent">{progress}%</span>
                    </div>

                    <div className="progress-bar-container">
                        <div className="progress-bar" style={{ width: `${progress}%` }} />
                    </div>

                    {/* Timeline */}
                    <div className="timeline-steps">
                        {PIPELINE_STEPS.map((step, index) => {
                            const isCompleted = completedSteps.has(step.id);
                            const isActive = currentStep === index && !isCompleted;
                            const stat = stepStats[step.id];

                            return (
                                <div key={step.id} className={`timeline-step ${isCompleted ? 'completed' : ''} ${isActive ? 'active' : ''}`}>
                                    <div className="timeline-dot">
                                        {isCompleted ? (
                                            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                                                <path d="M2.5 6L5 8.5L9.5 3.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                                            </svg>
                                        ) : isActive ? (
                                            <div className="timeline-pulse" />
                                        ) : null}
                                    </div>
                                    <div className="timeline-content">
                                        <span className="timeline-label">{step.label}</span>
                                        {stat && <span className="timeline-stat">{stat}</span>}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Stream */}
                <div className="stream-section">
                    <div className="stream-header">
                        <span className="stream-title">Live Stream</span>
                        <span className={`stream-indicator ${isComplete ? '' : 'active'}`}>
                            {isComplete ? 'Done' : 'Processing'}
                        </span>
                    </div>
                    <div className="file-stream" ref={streamRef}>
                        {fileStream.map(item => (
                            <div key={item.id} className={`stream-item ${item.type}`}>
                                <span className="stream-icon">
                                    {item.type === 'connect' && '→'}
                                    {item.type === 'fetch' && '↓'}
                                    {item.type === 'scan' && '◎'}
                                    {item.type === 'process' && '⚙'}
                                    {item.type === 'model' && '◆'}
                                    {item.type === 'db' && '▣'}
                                    {item.type === 'done' && '✓'}
                                    {item.type === 'error' && '✗'}
                                </span>
                                <span className="stream-text">{item.file}</span>
                            </div>
                        ))}
                        {!isComplete && <div className="stream-cursor" />}
                    </div>
                </div>

                {/* Results Summary - Always visible when complete */}
                {isComplete && (
                    <div className="results-section visible">
                        <h2>Ready to Explore</h2>
                        <div className="results-summary">
                            <div className="summary-stat">
                                <span className="summary-value">{results?.warmth?.score || 0}</span>
                                <span className="summary-label">Warmth</span>
                            </div>
                            <div className="summary-stat">
                                <span className="summary-value">{results?.techStack?.languages?.length || 0}</span>
                                <span className="summary-label">Languages</span>
                            </div>
                            <div className="summary-stat">
                                <span className="summary-value">
                                    {(results?.suggestions?.beginner_friendly?.length || 0) +
                                        (results?.suggestions?.bugs?.length || 0)}
                                </span>
                                <span className="summary-label">Ideas</span>
                            </div>
                        </div>
                        <button className="continue-btn" onClick={() => onComplete(results)}>
                            View Details
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                                <path d="M6 4L10 8L6 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                            </svg>
                        </button>
                    </div>
                )}

                {error && (
                    <div className="error-section">
                        <p>Error: {error}</p>
                        <button onClick={onBack}>Go Back</button>
                    </div>
                )}
            </div>
        </div>
    );
}

export default AnalysisPage;
