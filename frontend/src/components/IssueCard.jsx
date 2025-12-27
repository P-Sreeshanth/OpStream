function IssueCard({ issue, isActive, onSelect }) {
    return (
        <div
            className={`issue-card ${isActive ? 'active' : ''}`}
            onClick={onSelect}
        >
            <div className="issue-card-header">
                <span className="repo">{issue.repo_name}</span>
                {issue.stars > 0 && (
                    <span className="stars">★ {issue.stars.toLocaleString()}</span>
                )}
            </div>

            <h3>{issue.title}</h3>

            <div className="issue-tags">
                {issue.language && issue.language !== 'Unknown' && (
                    <span className="skill-tag lang">{issue.language}</span>
                )}
                {issue.labels?.slice(0, 2).map((label, i) => (
                    <span key={i} className="skill-tag label">{label}</span>
                ))}
            </div>

            <div className="meta">
                <span>{issue.comments} comments</span>
                <span>{issue.created_at?.split(' ')[0]}</span>
            </div>

            <a
                href={issue.url}
                target="_blank"
                rel="noopener noreferrer"
                className="link"
                onClick={(e) => e.stopPropagation()}
            >
                View on GitHub →
            </a>
        </div>
    );
}

export default IssueCard;
