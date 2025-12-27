import { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import DomainSelector from './components/DomainSelector';
import IssueCard from './components/IssueCard';
import ProjectPreview from './components/ProjectPreview';
import AnalysisPage from './components/AnalysisPage';
import ResultsPage from './components/ResultsPage';
import { api } from './config/api';

function App() {
  const [domains, setDomains] = useState([]);
  const [selectedDomain, setSelectedDomain] = useState(null);
  const [sortBy, setSortBy] = useState('recent');

  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Navigation state
  const [page, setPage] = useState('home');
  const [previewIssue, setPreviewIssue] = useState(null);
  const [analyzeIssue, setAnalyzeIssue] = useState(null);

  // Results state
  const [analysisResults, setAnalysisResults] = useState(null);
  const [activeRepo, setActiveRepo] = useState(null);

  useEffect(() => {
    fetch(api.domains())
      .then(res => res.json())
      .then(data => setDomains(data.domains || []))
      .catch(() => { });
  }, []);

  const searchIssues = async () => {
    setLoading(true);
    setError(null);
    setIssues([]);

    try {
      const res = await fetch(api.issues(), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          limit: 9,
          domain: selectedDomain,
          sort_by: sortBy
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Server error");
      setIssues(data.issues || []);
    } catch (err) {
      setError("Unable to connect. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  const openPreview = (issue) => {
    setPreviewIssue(issue);
  };

  const startAnalysis = (issue) => {
    setPreviewIssue(null);
    setAnalyzeIssue(issue);
    setPage('analyze');
  };

  const onAnalysisComplete = (results) => {
    setAnalysisResults(results);
    setActiveRepo(analyzeIssue.repo_name);
    setPage('results');
  };

  const goHome = () => {
    setPage('home');
    setAnalyzeIssue(null);
    setAnalysisResults(null);
    setActiveRepo(null);
  };

  // ANALYSIS PAGE
  if (page === 'analyze' && analyzeIssue) {
    return (
      <AnalysisPage
        issue={analyzeIssue}
        onComplete={onAnalysisComplete}
        onBack={goHome}
      />
    );
  }

  // RESULTS PAGE
  if (page === 'results' && analysisResults) {
    return (
      <ResultsPage
        repo={activeRepo}
        results={analysisResults}
        onBack={goHome}
      />
    );
  }

  // HOME PAGE
  return (
    <div className="app">
      <div className="gradient-bg" />

      <div className="content">
        <Navbar />

        <div className="container">
          <section className="hero">
            <span className="badge">Opstream</span>
            <h1>
              Find your first<br />
              <span className="gradient">contribution</span>
            </h1>
            <p>
              Discover beginner-friendly issues across popular open source projects.
              Get AI-powered insights to start contributing with confidence.
            </p>

            <DomainSelector
              domains={domains}
              selected={selectedDomain}
              onSelect={setSelectedDomain}
            />

            <div className="search-container">
              <div className="sort-toggle">
                <button
                  className={`sort-btn ${sortBy === 'recent' ? 'active' : ''}`}
                  onClick={() => setSortBy('recent')}
                >
                  Recent
                </button>
                <button
                  className={`sort-btn ${sortBy === 'popular' ? 'active' : ''}`}
                  onClick={() => setSortBy('popular')}
                >
                  Popular
                </button>
              </div>

              <button
                className="btn btn-primary"
                onClick={searchIssues}
                disabled={loading}
              >
                {loading ? 'Searching...' : 'Find Issues'}
              </button>
            </div>

            {error && <div className="error-banner">{error}</div>}
          </section>

          {issues.length > 0 && (
            <main className="main-content">
              <section className="section">
                <div className="section-header">
                  <h2>Issues</h2>
                  <span className="section-subtitle">
                    {issues.length} results • Click to preview
                  </span>
                </div>
                <div className="issues-grid">
                  {issues.map(issue => (
                    <IssueCard
                      key={issue.url}
                      issue={issue}
                      isActive={false}
                      onSelect={() => openPreview(issue)}
                    />
                  ))}
                </div>
              </section>
            </main>
          )}
        </div>
      </div>

      {previewIssue && (
        <ProjectPreview
          issue={previewIssue}
          onClose={() => setPreviewIssue(null)}
          onAnalyze={startAnalysis}
        />
      )}
    </div>
  );
}

export default App;
