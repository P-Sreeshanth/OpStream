function SetupPanel({ setup }) {
    if (!setup || (!setup.steps?.length && !setup.commands?.length)) {
        return null;
    }

    return (
        <div className="panel setup-panel">
            <h2>Getting started</h2>

            {setup.requirements?.length > 0 && (
                <div className="setup-section">
                    <h3>Requirements</h3>
                    <div className="requirements-list">
                        {setup.requirements.map((req, i) => (
                            <span key={i} className="requirement-tag">{req}</span>
                        ))}
                    </div>
                </div>
            )}

            {setup.steps?.length > 0 && (
                <div className="setup-section">
                    <h3>Setup</h3>
                    <ol className="steps-list">
                        {setup.steps.map((step, i) => (
                            <li key={i}>{step}</li>
                        ))}
                    </ol>
                </div>
            )}

            {setup.commands?.length > 0 && (
                <div className="setup-section">
                    <h3>Commands</h3>
                    <div className="commands-list">
                        {setup.commands.map((cmd, i) => (
                            <code key={i} className="command">$ {cmd}</code>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

export default SetupPanel;
