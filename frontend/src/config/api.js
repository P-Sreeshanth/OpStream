// API Configuration
// Uses environment variable in production, localhost in development

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// API endpoint helpers
export const api = {
    domains: () => `${API_URL}/api/domains`,
    issues: () => `${API_URL}/api/issues`,
    indexRepo: () => `${API_URL}/api/index-repo`,
    analyze: () => `${API_URL}/api/analyze`,
    suggest: () => `${API_URL}/api/suggest`,
    techStack: () => `${API_URL}/api/tech-stack`,
    setup: () => `${API_URL}/api/setup`,
    warmthScore: () => `${API_URL}/api/warmth-score`,
    contribute: () => `${API_URL}/api/contribute`,
    difficulty: () => `${API_URL}/api/difficulty`,
    relevantFiles: () => `${API_URL}/api/relevant-files`,
    issueSkills: () => `${API_URL}/api/issue-skills`,
    codeReview: () => `${API_URL}/api/code-review`,
    health: () => `${API_URL}/health`,
};

export default api;
