import { useState, useEffect } from 'react';

function ProjectPreview({ issue, onClose, onAnalyze }) {
    const [visible, setVisible] = useState(false);
    const [repoData, setRepoData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Trigger animation
        setTimeout(() => setVisible(true), 10);

        // Fetch quick repo info
        fetchRepoInfo();
    }, []);

    const fetchRepoInfo = async () => {
        try {
            // Quick fetch - just get what GitHub API gives us directly
            const res = await fetch(`https://api.github.com/repos/${issue.repo_name}`);
            if (res.ok) {
                const data = await res.json();
                setRepoData(data);
            }
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const handleClose = () => {
        setVisible(false);
        setTimeout(onClose, 300);
    };

    const handleAnalyze = () => {
        setVisible(false);
        setTimeout(() => onAnalyze(issue), 300);
    };

    return (
        <div className={`preview-overlay ${visible ? 'visible' : ''}`} onClick={handleClose}>
            <div className={`preview-modal ${visible ? 'visible' : ''}`} onClick={e => e.stopPropagation()}>

                {/* Animated gradient background */}
                <div className="preview-glow" />

                <button className="preview-close" onClick={handleClose}>×</button>

                {/* Header */}
                <div className="preview-header">
                    <div className="preview-repo-badge">
                        <span className="preview-icon">📦</span>
                        <span>{issue.repo_name}</span>
                    </div>
                    {repoData && (
                        <div className="preview-stats">
                            <span className="stat">★ {repoData.stargazers_count?.toLocaleString()}</span>
                            <span className="stat">🍴 {repoData.forks_count?.toLocaleString()}</span>
                            <span className="stat">👁 {repoData.watchers_count?.toLocaleString()}</span>
                        </div>
                    )}
                </div>

                {/* Issue Title */}
                <h2 className="preview-title">{issue.title}</h2>

                {/* Tags */}
                <div className="preview-tags">
                    {issue.language && issue.language !== 'Unknown' && (
                        <span className="preview-tag lang">{issue.language}</span>
                    )}
                    {issue.labels?.map((label, i) => (
                        <span key={i} className="preview-tag">{label}</span>
                    ))}
                </div>

                {/* Repository Description */}
                {loading ? (
                    <div className="preview-loading">
                        <div className="preview-skeleton" />
                        <div className="preview-skeleton short" />
                    </div>
                ) : repoData ? (
                    <div className="preview-content">
                        <p className="preview-desc">{repoData.description || 'No description available.'}</p>

                        <div className="preview-meta-grid">
                            <div className="preview-meta-item">
                                <span className="meta-label">Language</span>
                                <span className="meta-value">{repoData.language || 'Multiple'}</span>
                            </div>
                            <div className="preview-meta-item">
                                <span className="meta-label">Open Issues</span>
                                <span className="meta-value">{repoData.open_issues_count}</span>
                            </div>
                            <div className="preview-meta-item">
                                <span className="meta-label">License</span>
                                <span className="meta-value">{repoData.license?.spdx_id || 'None'}</span>
                            </div>
                            <div className="preview-meta-item">
                                <span className="meta-label">Created</span>
                                <span className="meta-value">{new Date(repoData.created_at).getFullYear()}</span>
                            </div>
                        </div>

                        {repoData.topics?.length > 0 && (
                            <div className="preview-topics">
                                {repoData.topics.slice(0, 6).map((topic, i) => (
                                    <span key={i} className="topic-tag">{topic}</span>
                                ))}
                            </div>
                        )}
                    </div>
                ) : (
                    <p className="preview-desc">Unable to load repository details.</p>
                )}

                {/* Actions */}
                <div className="preview-actions">
                    <a
                        href={issue.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="preview-btn secondary"
                    >
                        View Issue ↗
                    </a>
                    <button className="preview-btn primary" onClick={handleAnalyze}>
                        Analyze Repository →
                    </button>
                </div>
            </div>
        </div>
    );
}

export default ProjectPreview;
