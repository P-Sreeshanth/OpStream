function DomainSelector({ domains, selected, onSelect }) {
    if (!domains?.length) return null;

    return (
        <div className="domain-selector">
            <button
                className={`domain-chip ${!selected ? 'active' : ''}`}
                onClick={() => onSelect(null)}
            >
                All
            </button>
            {domains.map(domain => (
                <button
                    key={domain.id}
                    className={`domain-chip ${selected === domain.id ? 'active' : ''}`}
                    onClick={() => onSelect(domain.id)}
                >
                    {domain.label}
                </button>
            ))}
        </div>
    );
}

export default DomainSelector;
