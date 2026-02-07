import React, { useState, useMemo } from 'react';
import './LLMTimeline.css';

const LLMTimeline = ({ data }) => {
  const [selectedModel, setSelectedModel] = useState(null);
  const [filter, setFilter] = useState('all');
  const [sortBy, setSortBy] = useState('date');
  const [exportFormat, setExportFormat] = useState('json');

  // Sort and filter releases
  const processedReleases = useMemo(() => {
    let releases = [...data.releases];

    // Filter by company/provider
    if (filter !== 'all') {
      releases = releases.filter(r => r.provider === filter);
    }

    // Sort
    releases.sort((a, b) => {
      switch (sortBy) {
        case 'date':
          return new Date(a.releaseDate) - new Date(b.releaseDate);
        case 'date-desc':
          return new Date(b.releaseDate) - new Date(a.releaseDate);
        case 'name':
          return a.name.localeCompare(b.name);
        case 'params':
          const getParamValue = (p) => {
            const num = parseInt(p);
            if (p.includes('T')) return num * 1000;
            if (p.includes('B')) return num;
            if (p.includes('M')) return num / 1000;
            return 0;
          };
          return getParamValue(b.parameters || '0') - getParamValue(a.parameters || '0');
        default:
          return 0;
      }
    });

    return releases;
  }, [data.releases, filter, sortBy]);

  // Get unique providers
  const providers = useMemo(() => {
    return ['all', ...new Set(data.releases.map(r => r.provider))].sort();
  }, [data.releases]);

  // Format date
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  // Export functions
  const handleExport = async () => {
    const exportData = {
      timestamp: new Date().toISOString(),
      models: processedReleases,
      metadata: data.metadata
    };

    let content, filename, type;

    switch (exportFormat) {
      case 'json':
        content = JSON.stringify(exportData, null, 2);
        filename = 'llm_timeline.json';
        type = 'application/json';
        break;

      case 'csv':
        const headers = ['Model Name', 'Release Date', 'Company', 'Parameters', 'Context Window', 'Modality'];
        const rows = processedReleases.map(m => [
          m.name,
          formatDate(m.releaseDate),
          m.provider,
          m.parameters || 'N/A',
          m.context_window || 'N/A',
          (m.modality || []).join('; ')
        ]);
        content = [headers, ...rows].map(r => r.map(c => `"${c}"`).join(',')).join('\n');
        filename = 'llm_timeline.csv';
        type = 'text/csv';
        break;

      case 'markdown':
        content = `# LLM Timeline\n\nExported: ${new Date().toISOString()}\n\n`;
        content += `| Model | Date | Company | Parameters |\n`;
        content += `|-------|------|---------|------------|\n`;
        processedReleases.forEach(m => {
          content += `| ${m.name} | ${formatDate(m.releaseDate)} | ${m.provider} | ${m.parameters || 'N/A'} |\n`;
        });
        filename = 'llm_timeline.md';
        type = 'text/markdown';
        break;

      default:
        return;
    }

    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="llm-timeline">
      {/* Header */}
      <div className="timeline-header">
        <h1 className="timeline-title">AI/LLM Model Releases</h1>
        <p className="timeline-subtitle">A professional timeline of major LLM releases since GPT-2</p>
      </div>

      {/* Controls */}
      <div className="timeline-controls">
        <div className="control-group">
          <label htmlFor="provider-filter">Filter by Provider:</label>
          <select 
            id="provider-filter"
            value={filter} 
            onChange={(e) => setFilter(e.target.value)}
            className="control-select"
          >
            {providers.map(p => (
              <option key={p} value={p}>
                {p === 'all' ? 'All Providers' : p}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label htmlFor="sort-by">Sort by:</label>
          <select 
            id="sort-by"
            value={sortBy} 
            onChange={(e) => setSortBy(e.target.value)}
            className="control-select"
          >
            <option value="date">Oldest First</option>
            <option value="date-desc">Newest First</option>
            <option value="name">Name</option>
            <option value="params">Parameters (Largest)</option>
          </select>
        </div>

        <div className="control-group">
          <label htmlFor="export-format">Export as:</label>
          <select 
            id="export-format"
            value={exportFormat} 
            onChange={(e) => setExportFormat(e.target.value)}
            className="control-select"
          >
            <option value="json">JSON</option>
            <option value="csv">CSV</option>
            <option value="markdown">Markdown</option>
          </select>
        </div>

        <button onClick={handleExport} className="export-btn">
          ⬇ Export
        </button>
      </div>

      {/* Timeline */}
      <div className="timeline-container">
        <div className="timeline-line"></div>
        
        <div className="timeline-items">
          {processedReleases.map((release, index) => (
            <div 
              key={release.id} 
              className={`timeline-item ${index % 2 === 0 ? 'left' : 'right'} ${selectedModel?.id === release.id ? 'active' : ''}`}
              onClick={() => setSelectedModel(selectedModel?.id === release.id ? null : release)}
            >
              <div className="timeline-dot"></div>
              
              <div className="timeline-content">
                <div className="model-header">
                  <h3 className="model-name">{release.name}</h3>
                  <span className="model-date">{formatDate(release.releaseDate)}</span>
                </div>

                <div className="model-meta">
                  <span className="provider-badge">{release.provider}</span>
                  <span className="modality-badges">
                    {(release.modality || []).map(m => (
                      <span key={m} className={`modality-badge modality-${m}`}>
                        {m}
                      </span>
                    ))}
                  </span>
                </div>

                <div className="model-specs">
                  {release.parameters && <span>📊 {release.parameters}</span>}
                  {release.context_window && <span>📈 {release.context_window}K</span>}
                  {release.architecture && <span>🔧 {release.architecture}</span>}
                </div>

                {/* Expanded details */}
                {selectedModel?.id === release.id && (
                  <div className="model-details">
                    {release.features && release.features.length > 0 && (
                      <div className="detail-section">
                        <h4>Features</h4>
                        <ul>
                          {release.features.map((f, i) => <li key={i}>{f}</li>)}
                        </ul>
                      </div>
                    )}

                    {release.notableAchievements && release.notableAchievements.length > 0 && (
                      <div className="detail-section">
                        <h4>Notable Achievements</h4>
                        <ul>
                          {release.notableAchievements.map((a, i) => <li key={i}>{a}</li>)}
                        </ul>
                      </div>
                    )}

                    {release.trainingData && (
                      <div className="detail-section">
                        <h4>Training Data</h4>
                        <p>{release.trainingData}</p>
                      </div>
                    )}

                    {release.documentation && (
                      <div className="detail-section">
                        <a href={release.documentation} target="_blank" rel="noopener noreferrer" className="doc-link">
                          📚 Read Documentation
                        </a>
                      </div>
                    )}

                    <p className="access-info">
                      {release.publicAccess ? '🔓 Open Source' : '🔒 Closed Source'}
                      {release.apiAvailable && ' • API Available'}
                    </p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Statistics */}
      <div className="timeline-stats">
        <div className="stat-card">
          <span className="stat-number">{processedReleases.length}</span>
          <span className="stat-label">Models</span>
        </div>
        <div className="stat-card">
          <span className="stat-number">{new Set(processedReleases.map(r => r.provider)).size}</span>
          <span className="stat-label">Providers</span>
        </div>
        <div className="stat-card">
          <span className="stat-number">
            {new Set(processedReleases.flatMap(r => r.modality || [])).size}
          </span>
          <span className="stat-label">Modalities</span>
        </div>
      </div>
    </div>
  );
};

export default LLMTimeline;
