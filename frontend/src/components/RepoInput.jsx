import { useState } from 'react';

function RepoInput({ onSubmit, loading, indexedRepos, onSelectRepo }) {
    const [url, setUrl] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (url.trim()) {
            onSubmit(url.trim());
        }
    };

    return (
        <section className="repo-input-section glass-panel">
            <form onSubmit={handleSubmit} className="repo-form">
                <div className="input-wrapper">
                    <span className="input-icon">🔗</span>
                    <input
                        type="text"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        placeholder="Enter GitHub repository URL (e.g., https://github.com/fastapi/fastapi)"
                        className="repo-input"
                        disabled={loading}
                    />
                </div>
                <button type="submit" className="btn" disabled={loading}>
                    {loading ? (
                        <>
                            <span className="spinner"></span>
                            Indexing...
                        </>
                    ) : (
                        '🚀 Index Repository'
                    )}
                </button>
            </form>

            {indexedRepos.length > 0 && (
                <div className="indexed-repos">
                    <span className="repos-label">Indexed:</span>
                    {indexedRepos.map(repo => (
                        <button
                            key={repo}
                            className="repo-chip"
                            onClick={() => onSelectRepo(repo)}
                        >
                            📦 {repo}
                        </button>
                    ))}
                </div>
            )}
        </section>
    );
}

export default RepoInput;
