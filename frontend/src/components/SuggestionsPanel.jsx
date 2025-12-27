function SuggestionsPanel({ suggestions }) {
    if (!suggestions) return null;

    const categories = [
        { key: 'beginner_friendly', title: 'Beginner Friendly' },
        { key: 'documentation', title: 'Documentation' },
        { key: 'bugs', title: 'Bug Fixes' },
        { key: 'features', title: 'Features' }
    ];

    return (
        <div className="panel">
            <h2>Contribution ideas</h2>

            {suggestions.summary && (
                <p className="summary-text">{suggestions.summary}</p>
            )}

            <div className="suggestions-list">
                {categories.map(cat => {
                    const items = suggestions[cat.key] || [];
                    if (items.length === 0) return null;

                    return (
                        <div key={cat.key}>
                            <h3>{cat.title}</h3>
                            <ul>
                                {items.slice(0, 4).map((item, i) => (
                                    <li key={i}>{item}</li>
                                ))}
                            </ul>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

export default SuggestionsPanel;
