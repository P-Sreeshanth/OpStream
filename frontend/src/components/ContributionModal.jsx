import { useState } from 'react';
import confetti from 'canvas-confetti';
import { api } from '../config/api';

function ContributionModal({ issue, onClose }) {
    const [status, setStatus] = useState('idle'); // idle, working, success, error
    const [logs, setLogs] = useState([]);
    const [prUrl, setPrUrl] = useState(null);

    const addLog = (msg) => setLogs(prev => [...prev, `> ${msg}`]);

    // Confetti celebration effect
    const celebrate = () => {
        const duration = 3000;
        const end = Date.now() + duration;

        const frame = () => {
            confetti({
                particleCount: 3,
                angle: 60,
                spread: 55,
                origin: { x: 0 },
                colors: ['#8b5cf6', '#06b6d4', '#ffffff']
            });
            confetti({
                particleCount: 3,
                angle: 120,
                spread: 55,
                origin: { x: 1 },
                colors: ['#8b5cf6', '#06b6d4', '#ffffff']
            });

            if (Date.now() < end) {
                requestAnimationFrame(frame);
            }
        };
        frame();
    };

    const startContribution = async () => {
        setStatus('working');
        setLogs([]);
        addLog(`Initializing AI Agent for issue #${issue.number}...`);
        addLog(`Target Repo: ${issue.repo_name}`);

        try {
            setTimeout(() => addLog("Cloning repository (shallow)..."), 500);
            setTimeout(() => addLog("Analyzing file structure..."), 1500);
            setTimeout(() => addLog("Reading issue description..."), 2500);
            setTimeout(() => addLog("Generating patch with GLM-4 Model..."), 4000);

            const res = await fetch(api.contribute(), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    issue_url: issue.url,
                    user_id: 12345
                })
            });

            const data = await res.json();

            if (!res.ok) throw new Error(data.detail || "Failed");

            addLog("Patch applied successfully.");
            addLog("Pushing changes to fork...");
            addLog("Opening Pull Request...");

            setStatus('success');
            setPrUrl(data.pr_url);

            // 🎉 Trigger confetti celebration!
            celebrate();

        } catch (err) {
            setStatus('error');
            addLog(`ERROR: ${err.message}`);
        }
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content glass-panel" onClick={e => e.stopPropagation()}>
                <h2>Automated Contribution</h2>
                <p>You are about to fix <strong>{issue.title}</strong></p>

                <div className="terminal-log">
                    {logs.map((log, i) => <div key={i}>{log}</div>)}
                    {status === 'working' && <span className="animate-pulse">_</span>}
                </div>

                <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
                    {status === 'idle' && (
                        <button className="btn" onClick={startContribution}>
                            Confirm & Fix
                        </button>
                    )}

                    {status === 'success' && (
                        <a href={prUrl} target="_blank" rel="noreferrer" className="btn">
                            🎉 View Pull Request
                        </a>
                    )}

                    <button className="btn btn-secondary" onClick={onClose}>
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
}

export default ContributionModal;
