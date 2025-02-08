from typing import Dict, List, Optional
from datetime import datetime
import json

class SummaryManager:
    def __init__(self):
        self.summaries: Dict[str, dict] = {}
    
    def update_summary(self, uuid: str, content: str) -> None:
        """
        Updates or creates a summary for a specific UUID
        """
        if uuid not in self.summaries:
            self.summaries[uuid] = {
                'content': content,
                'history': [{
                    'content': content,
                    'timestamp': datetime.now().isoformat()
                }]
            }
        else:
            existing = self.summaries[uuid]
            if existing['content'] != content:
                existing['content'] = content
                existing['history'].append({
                    'content': content,
                    'timestamp': datetime.now().isoformat()
                })

    def get_summary(self, uuid: str) -> Optional[dict]:
        """
        Retrieves summary data for a specific UUID
        """
        return self.summaries.get(uuid)

    def get_all_summaries(self) -> Dict[str, dict]:
        """
        Returns all summaries
        """
        return self.summaries

    def delete_summary(self, uuid: str) -> None:
        """
        Deletes a summary by UUID
        """
        if uuid in self.summaries:
            del self.summaries[uuid]

    def save_to_file(self, filepath: str) -> None:
        """
        Saves summaries to a JSON file
        """
        with open(filepath, 'w') as f:
            json.dump(self.summaries, f, indent=2)

    def load_from_file(self, filepath: str) -> None:
        """
        Loads summaries from a JSON file
        """
        try:
            with open(filepath, 'r') as f:
                self.summaries = json.load(f)
        except FileNotFoundError:
            self.summaries = {}

# Example usage:
"""
manager = SummaryManager()

# Load existing summaries
manager.load_from_file('summaries.json')

# Update a specific summary
manager.update_summary(
    uuid='123',
    content='This is a summary of the research findings...'
)

# Get a specific summary
summary = manager.get_summary('123')

# Save all summaries
manager.save_to_file('summaries.json')
"""
