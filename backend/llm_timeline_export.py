#!/usr/bin/env python3
"""
LLM Timeline Export Utility
Converts LLM release data to multiple formats: JSON, CSV, Markdown, and more.
"""

import json
import csv
import os
from datetime import datetime
from typing import List, Dict, Any


class LLMTimelineExporter:
    def __init__(self, json_file_path: str):
        """Initialize with JSON data file."""
        with open(json_file_path, 'r') as f:
            self.data = json.load(f)
        self.releases = self.data.get('releases', [])
        self.output_dir = os.path.dirname(json_file_path)

    def export_json(self, filename: str = "llm_timeline.json") -> str:
        """Export as pretty JSON."""
        output_path = os.path.join(self.output_dir, filename)
        with open(output_path, 'w') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        return output_path

    def export_csv(self, filename: str = "llm_timeline.csv") -> str:
        """Export as CSV with key information."""
        output_path = os.path.join(self.output_dir, filename)
        
        fieldnames = [
            'Model Name',
            'Release Date',
            'Company/Provider',
            'Parameters',
            'Context Window',
            'Architecture',
            'Modality',
            'Model Type',
            'Public Access',
            'Features',
            'Notable Achievements'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for release in self.releases:
                writer.writerow({
                    'Model Name': release.get('name', ''),
                    'Release Date': release.get('releaseDate', ''),
                    'Company/Provider': f"{release.get('company', '')} / {release.get('provider', '')}",
                    'Parameters': release.get('parameters', ''),
                    'Context Window': release.get('context_window', ''),
                    'Architecture': release.get('architecture', ''),
                    'Modality': ', '.join(release.get('modality', [])),
                    'Model Type': release.get('modelType', ''),
                    'Public Access': 'Yes' if release.get('publicAccess') else 'No',
                    'Features': ', '.join(release.get('features', [])),
                    'Notable Achievements': ', '.join(release.get('notableAchievements', []))
                })
        
        return output_path

    def export_markdown(self, filename: str = "llm_timeline.md") -> str:
        """Export as Markdown table."""
        output_path = os.path.join(self.output_dir, filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# AI/LLM Model Releases Timeline\n\n")
            f.write(f"*Last Updated: {self.data['metadata']['lastUpdated']}*\n\n")
            f.write("## Overview\n\n")
            f.write(f"Total Models Tracked: {len(self.releases)}\n\n")
            
            f.write("## Timeline\n\n")
            f.write("| Model Name | Release Date | Company | Parameters | Context | Architecture | Modality |\n")
            f.write("|------------|--------------|---------|------------|---------|--------------|----------|\n")
            
            for release in sorted(self.releases, key=lambda x: x['releaseDate']):
                date_obj = datetime.fromisoformat(release['releaseDate'].replace('Z', '+00:00'))
                formatted_date = date_obj.strftime('%Y-%m-%d')
                
                f.write(
                    f"| {release['name']} | {formatted_date} | "
                    f"{release['provider']} | {release.get('parameters', 'N/A')} | "
                    f"{release.get('context_window', 'N/A')} | {release.get('architecture', 'N/A')} | "
                    f"{', '.join(release.get('modality', []))} |\n"
                )
            
            # Detailed section
            f.write("\n## Detailed Information\n\n")
            for release in sorted(self.releases, key=lambda x: x['releaseDate']):
                f.write(self._format_model_details(release))
        
        return output_path

    def export_ndjson(self, filename: str = "llm_timeline.ndjson") -> str:
        """Export as newline-delimited JSON (one record per line)."""
        output_path = os.path.join(self.output_dir, filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for release in self.releases:
                f.write(json.dumps(release, ensure_ascii=False) + '\n')
        
        return output_path

    def export_html_snippet(self, filename: str = "llm_timeline.html") -> str:
        """Export as HTML table snippet."""
        output_path = os.path.join(self.output_dir, filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM Releases Timeline</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #f5f5f5; font-weight: 600; }
        tr:hover { background-color: #f9f9f9; }
        .date { font-weight: 600; color: #0066cc; }
        .modal-type { display: inline-block; background: #e8f4f8; padding: 4px 8px; border-radius: 3px; font-size: 0.85em; }
    </style>
</head>
<body>
    <h1>AI/LLM Model Releases Timeline</h1>
    <table>
        <thead>
            <tr>
                <th>Model Name</th>
                <th>Release Date</th>
                <th>Company</th>
                <th>Parameters</th>
                <th>Context</th>
                <th>Modality</th>
                <th>Type</th>
            </tr>
        </thead>
        <tbody>
""")
            
            for release in sorted(self.releases, key=lambda x: x['releaseDate']):
                date_obj = datetime.fromisoformat(release['releaseDate'].replace('Z', '+00:00'))
                formatted_date = date_obj.strftime('%Y-%m-%d')
                modality_tags = ' '.join(
                    f'<span class="modal-type">{m}</span>' 
                    for m in release.get('modality', [])
                )
                
                f.write(f"""            <tr>
                <td><strong>{release['name']}</strong></td>
                <td class="date">{formatted_date}</td>
                <td>{release['provider']}</td>
                <td>{release['parameters']}</td>
                <td>{release['context_window']}</td>
                <td>{modality_tags}</td>
                <td>{release['modelType']}</td>
            </tr>
""")
            
            f.write("""        </tbody>
    </table>
</body>
</html>
""")
        
        return output_path

    def export_yaml(self, filename: str = "llm_timeline.yaml") -> str:
        """Export as YAML format."""
        output_path = os.path.join(self.output_dir, filename)
        
        try:
            import yaml
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        except ImportError:
            # Fallback: create YAML-like format manually
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("metadata:\n")
                f.write(f"  title: {self.data['metadata']['title']}\n")
                f.write(f"  description: {self.data['metadata']['description']}\n")
                f.write(f"  lastUpdated: {self.data['metadata']['lastUpdated']}\n\n")
                f.write("releases:\n")
                
                for release in self.releases:
                    f.write(f"  - id: {release['id']}\n")
                    f.write(f"    name: {release['name']}\n")
                    f.write(f"    releaseDate: {release['releaseDate']}\n")
                    f.write(f"    company: {release['company']}\n")
                    f.write(f"    provider: {release['provider']}\n")
                    f.write(f"    parameters: {release.get('parameters', 'Unknown')}\n")
                    f.write(f"    contextWindow: {release.get('context_window', 'N/A')}\n")
                    f.write(f"    modality: {release.get('modality', [])}\n")
        
        return output_path

    def export_stats_json(self, filename: str = "llm_timeline_stats.json") -> str:
        """Export statistics as JSON."""
        output_path = os.path.join(self.output_dir, filename)
        
        # Calculate statistics
        total_models = len(self.releases)
        companies = {}
        modality_counts = {}
        
        for release in self.releases:
            company = release['provider']
            companies[company] = companies.get(company, 0) + 1
            
            for mod in release.get('modality', []):
                modality_counts[mod] = modality_counts.get(mod, 0) + 1
        
        stats = {
            "total_models": total_models,
            "companies": companies,
            "modality_distribution": modality_counts,
            "earliest_release": min(r['releaseDate'] for r in self.releases),
            "latest_release": max(r['releaseDate'] for r in self.releases),
            "by_parameter_size": self._group_by_parameters(),
            "by_year": self._group_by_year()
        }
        
        with open(output_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        return output_path

    def _group_by_parameters(self) -> Dict[str, int]:
        """Group models by parameter size."""
        groups = {}
        for release in self.releases:
            params = release.get('parameters', 'Unknown')
            groups[params] = groups.get(params, 0) + 1
        return groups

    def _group_by_year(self) -> Dict[str, int]:
        """Group models by release year."""
        groups = {}
        for release in self.releases:
            date_obj = datetime.fromisoformat(release['releaseDate'].replace('Z', '+00:00'))
            year = str(date_obj.year)
            groups[year] = groups.get(year, 0) + 1
        return dict(sorted(groups.items()))

    def _format_model_details(self, release: Dict[str, Any]) -> str:
        """Format detailed information for a single model."""
        date_obj = datetime.fromisoformat(release['releaseDate'].replace('Z', '+00:00'))
        formatted_date = date_obj.strftime('%B %d, %Y')
        
        details = f"### {release['name']}\n\n"
        details += f"**Release Date:** {formatted_date}\n\n"
        details += f"**Company:** {release['company']} | **Provider:** {release['provider']}\n\n"
        
        details += "**Specifications:**\n"
        details += f"- Parameters: {release.get('parameters', 'Unknown')}\n"
        details += f"- Context Window: {release.get('context_window', 'N/A')} tokens\n"
        details += f"- Architecture: {release.get('architecture', 'N/A')}\n"
        details += f"- Modality: {', '.join(release.get('modality', []))}\n"
        details += f"- Model Type: {release['modelType']}\n"
        details += f"- Public Access: {'Yes' if release.get('publicAccess') else 'No'}\n\n"
        
        if release.get('features'):
            details += "**Features:**\n"
            for feature in release['features']:
                details += f"- {feature}\n"
            details += "\n"
        
        if release.get('notableAchievements'):
            details += "**Notable Achievements:**\n"
            for achievement in release['notableAchievements']:
                details += f"- {achievement}\n"
            details += "\n"
        
        if release.get('documentation'):
            details += f"**Documentation:** [{release['documentation']}]({release['documentation']})\n\n"
        
        details += "---\n\n"
        return details

    def export_all(self) -> Dict[str, str]:
        """Export in all supported formats."""
        results = {}
        
        formats = [
            ('json', self.export_json),
            ('csv', self.export_csv),
            ('markdown', self.export_markdown),
            ('ndjson', self.export_ndjson),
            ('html', self.export_html_snippet),
            ('yaml', self.export_yaml),
            ('stats', self.export_stats_json)
        ]
        
        for format_name, export_func in formats:
            try:
                path = export_func()
                results[format_name] = path
                print(f"✓ Exported {format_name}: {path}")
            except Exception as e:
                print(f"✗ Failed to export {format_name}: {e}")
                results[format_name] = None
        
        return results


if __name__ == "__main__":
    import sys
    
    json_file = sys.argv[1] if len(sys.argv) > 1 else "llm_releases.json"
    
    exporter = LLMTimelineExporter(json_file)
    results = exporter.export_all()
    
    print("\n" + "="*50)
    print("Export Complete!")
    print("="*50)
    for format_name, path in results.items():
        if path:
            print(f"{format_name.upper()}: {path}")
