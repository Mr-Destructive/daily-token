"""
LLM Timeline API Backend
Provides REST API endpoints for the LLM Timeline feature.

Usage:
    from llm_timeline_api import register_llm_timeline_routes
    
    app = Flask(__name__)
    register_llm_timeline_routes(app)
"""

import json
import os
from datetime import datetime
from flask import Flask, jsonify, request, send_file, current_app
from functools import lru_cache


class LLMTimelineAPI:
    """API handler for LLM Timeline data."""
    
    def __init__(self, json_file_path: str = None):
        """Initialize with path to LLM releases JSON file."""
        if json_file_path is None:
            json_file_path = os.path.join(
                os.path.dirname(__file__), 
                'llm_releases.json'
            )
        self.json_file_path = json_file_path
        self._load_data()
    
    def _load_data(self):
        """Load and cache the timeline data."""
        with open(self.json_file_path, 'r') as f:
            self.data = json.load(f)
        self.releases = self.data.get('releases', [])
    
    def reload_data(self):
        """Reload data from file (for updates)."""
        self._load_data()
    
    def get_all_releases(self, filters: dict = None) -> dict:
        """
        Get all releases with optional filters.
        
        Filters:
            provider: Filter by company (OpenAI, Meta, Google, etc.)
            modality: Filter by modality (text, image, audio, video)
            year: Filter by release year
            public: Filter by public access (true/false)
        
        Returns:
            Dictionary with metadata and filtered releases
        """
        releases = self.releases.copy()
        
        if filters:
            # Filter by provider
            if 'provider' in filters:
                provider = filters['provider']
                releases = [r for r in releases if r['provider'] == provider]
            
            # Filter by modality
            if 'modality' in filters:
                modality = filters['modality']
                releases = [r for r in releases 
                           if modality in r.get('modality', [])]
            
            # Filter by year
            if 'year' in filters:
                year = int(filters['year'])
                releases = [r for r in releases 
                           if datetime.fromisoformat(
                               r['releaseDate'].replace('Z', '+00:00')
                           ).year == year]
            
            # Filter by public access
            if 'public' in filters:
                is_public = filters['public'].lower() == 'true'
                releases = [r for r in releases 
                           if r.get('publicAccess') == is_public]
        
        return {
            'metadata': self.data['metadata'],
            'count': len(releases),
            'releases': releases
        }
    
    def get_release_by_id(self, model_id: str) -> dict:
        """Get a specific release by model ID."""
        for release in self.releases:
            if release['id'] == model_id:
                return release
        return None
    
    def get_providers(self) -> list:
        """Get list of all unique providers."""
        providers = set(r['provider'] for r in self.releases)
        return sorted(list(providers))
    
    def get_modalities(self) -> list:
        """Get list of all unique modalities."""
        modalities = set()
        for r in self.releases:
            modalities.update(r.get('modality', []))
        return sorted(list(modalities))
    
    def get_statistics(self) -> dict:
        """Get statistics about the timeline."""
        by_provider = {}
        by_modality = {}
        by_year = {}
        
        for release in self.releases:
            # Count by provider
            provider = release['provider']
            by_provider[provider] = by_provider.get(provider, 0) + 1
            
            # Count by modality
            for modality in release.get('modality', []):
                by_modality[modality] = by_modality.get(modality, 0) + 1
            
            # Count by year
            date_obj = datetime.fromisoformat(
                release['releaseDate'].replace('Z', '+00:00')
            )
            year = str(date_obj.year)
            by_year[year] = by_year.get(year, 0) + 1
        
        return {
            'total_models': len(self.releases),
            'total_providers': len(set(r['provider'] for r in self.releases)),
            'total_modalities': len(by_modality),
            'models_by_provider': by_provider,
            'models_by_modality': by_modality,
            'models_by_year': dict(sorted(by_year.items())),
            'earliest_release': min(r['releaseDate'] for r in self.releases),
            'latest_release': max(r['releaseDate'] for r in self.releases),
        }
    
    def search(self, query: str) -> list:
        """Search for models by name or features."""
        query = query.lower()
        results = []
        
        for release in self.releases:
            # Search in name
            if query in release['name'].lower():
                results.append(release)
                continue
            
            # Search in features
            if any(query in f.lower() for f in release.get('features', [])):
                results.append(release)
                continue
            
            # Search in achievements
            if any(query in a.lower() 
                   for a in release.get('notableAchievements', [])):
                results.append(release)
        
        return results


def register_llm_timeline_routes(app: Flask, json_file_path: str = None):
    """
    Register LLM Timeline API routes with Flask app.
    
    Usage:
        app = Flask(__name__)
        register_llm_timeline_routes(app)
    """
    
    api = LLMTimelineAPI(json_file_path)
    
    @app.route('/api/llm-timeline', methods=['GET'])
    def get_timeline():
        """Get all LLM releases with optional filters."""
        filters = {}
        
        # Collect filter parameters
        for param in ['provider', 'modality', 'year', 'public']:
            if request.args.get(param):
                filters[param] = request.args.get(param)
        
        result = api.get_all_releases(filters if filters else None)
        return jsonify(result)
    
    @app.route('/api/llm-timeline/<model_id>', methods=['GET'])
    def get_model(model_id: str):
        """Get a specific model by ID."""
        model = api.get_release_by_id(model_id)
        if model:
            return jsonify(model)
        return jsonify({'error': 'Model not found'}), 404
    
    @app.route('/api/llm-timeline/providers', methods=['GET'])
    def get_providers():
        """Get list of all providers."""
        return jsonify({'providers': api.get_providers()})
    
    @app.route('/api/llm-timeline/modalities', methods=['GET'])
    def get_modalities():
        """Get list of all modalities."""
        return jsonify({'modalities': api.get_modalities()})
    
    @app.route('/api/llm-timeline/stats', methods=['GET'])
    def get_stats():
        """Get timeline statistics."""
        return jsonify(api.get_statistics())
    
    @app.route('/api/llm-timeline/search', methods=['GET'])
    def search():
        """Search for models."""
        query = request.args.get('q', '')
        if not query or len(query) < 2:
            return jsonify({'error': 'Query too short'}), 400
        
        results = api.search(query)
        return jsonify({
            'query': query,
            'count': len(results),
            'results': results
        })
    
    @app.route('/api/llm-timeline/export', methods=['GET'])
    def export_data():
        """Export timeline data in various formats."""
        format_type = request.args.get('format', 'json').lower()
        
        # Map format to file
        export_files = {
            'json': os.path.join(os.path.dirname(__file__), 'llm_timeline.json'),
            'csv': os.path.join(os.path.dirname(__file__), 'llm_timeline.csv'),
            'markdown': os.path.join(os.path.dirname(__file__), 'llm_timeline.md'),
            'ndjson': os.path.join(os.path.dirname(__file__), 'llm_timeline.ndjson'),
            'html': os.path.join(os.path.dirname(__file__), 'llm_timeline.html'),
            'yaml': os.path.join(os.path.dirname(__file__), 'llm_timeline.yaml'),
        }
        
        if format_type not in export_files:
            return jsonify({'error': 'Invalid format'}), 400
        
        file_path = export_files[format_type]
        if not os.path.exists(file_path):
            return jsonify({'error': 'Export file not found'}), 404
        
        # Determine MIME type
        mime_types = {
            'json': 'application/json',
            'csv': 'text/csv',
            'markdown': 'text/markdown',
            'ndjson': 'application/x-ndjson',
            'html': 'text/html',
            'yaml': 'text/yaml',
        }
        
        return send_file(
            file_path,
            mimetype=mime_types[format_type],
            as_attachment=True,
            download_name=f'llm_timeline.{format_type}'
        )
    
    return api


if __name__ == '__main__':
    # Test the API locally
    from flask_cors import CORS
    
    app = Flask(__name__)
    CORS(app)
    
    # Register routes
    api = register_llm_timeline_routes(app)
    
    print(f"Loaded {len(api.releases)} LLM models")
    print(f"Providers: {', '.join(api.get_providers())}")
    print(f"Modalities: {', '.join(api.get_modalities())}")
    
    # Run development server
    app.run(debug=True, port=5000)
