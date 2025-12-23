"""
Shared Brain - Claude-to-Claude Knowledge Sharing
==================================================
A shared knowledge base between Rev's Claude and G14's Claude.

Usage:
    from shared_brain import brain

    # Save something
    brain.save("def hello(): print('hi')", type="snippet", language="python",
               tags=["greeting", "simple"], description="Basic hello function")

    # Save a lesson learned
    brain.learn("Always backup before editing - GLOB FIRST to find highest backup number")

    # Get recent entries
    entries = brain.recent(limit=10)

    # Search by type
    snippets = brain.get(type="snippet")
    lessons = brain.get(type="lesson")

    # Search by tag
    python_stuff = brain.search(tag="python")
"""

import os
import requests
from datetime import datetime

# Supabase config - env vars with fallback to hardcoded (for backwards compatibility)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://yjyryzlbkbtdzguvqegt.supabase.co")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlqeXJ5emxia2J0ZHpndXZxZWd0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk0NTMzOTYsImV4cCI6MjA3NTAyOTM5Nn0.Vujw3q9_iHj4x5enf42V-7g355Tnzp9zdsoNYVCV8TY")

# Author identifier - env var or default to R (Rev's Claude). G14's Claude should set CLAUDE_AUTHOR=G
AUTHOR = os.environ.get("CLAUDE_AUTHOR", "R")

class SharedBrain:
    def __init__(self, author=AUTHOR):
        self.author = author
        self.base_url = f"{SUPABASE_URL}/rest/v1/shared_knowledge"
        self.headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    def save(self, content, type="snippet", language=None, tags=None, description=None):
        """Save knowledge to the shared brain.

        Args:
            content: The actual content (code, text, lesson, etc.)
            type: One of: snippet, lesson, discovery, bug_fix, pattern
            language: Programming language (python, javascript, sql, etc.)
            tags: List of tags for categorization
            description: Brief description of what this is

        Returns:
            The created entry or error dict
        """
        data = {
            "author": self.author,
            "type": type,
            "content": content,
            "language": language,
            "tags": tags or [],
            "description": description
        }

        try:
            resp = requests.post(self.base_url, json=data, headers=self.headers, timeout=10)
            if resp.status_code == 201:
                result = resp.json()
                print(f"Saved {type}: {description or content[:50]}...")
                return result[0] if result else {"status": "saved"}
            else:
                return {"error": resp.text, "status_code": resp.status_code}
        except Exception as e:
            return {"error": str(e)}

    def learn(self, lesson, tags=None):
        """Quick method to save a lesson learned."""
        return self.save(lesson, type="lesson", tags=tags, description=lesson[:100])

    def discover(self, discovery, tags=None):
        """Quick method to save a discovery."""
        return self.save(discovery, type="discovery", tags=tags, description=discovery[:100])

    def snippet(self, code, language, description=None, tags=None):
        """Quick method to save a code snippet."""
        return self.save(code, type="snippet", language=language, tags=tags, description=description)

    def recent(self, limit=20):
        """Get recent entries from both Claudes."""
        try:
            url = f"{self.base_url}?order=created_at.desc&limit={limit}"
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            return {"error": resp.text}
        except Exception as e:
            return {"error": str(e)}

    def get(self, type=None, author=None, limit=50):
        """Get entries filtered by type and/or author."""
        try:
            url = f"{self.base_url}?order=created_at.desc&limit={limit}"
            if type:
                url += f"&type=eq.{type}"
            if author:
                url += f"&author=eq.{author}"
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            return {"error": resp.text}
        except Exception as e:
            return {"error": str(e)}

    def search(self, tag=None, language=None, query=None, limit=50):
        """Search entries by tag, language, or text content."""
        try:
            url = f"{self.base_url}?order=created_at.desc&limit={limit}"
            if tag:
                url += f"&tags=cs.{{{tag}}}"  # Array contains
            if language:
                url += f"&language=eq.{language}"
            # Note: Full text search would need a different setup
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                results = resp.json()
                # Client-side filter for query if provided
                if query and results:
                    query_lower = query.lower()
                    results = [r for r in results if
                              query_lower in r.get('content', '').lower() or
                              query_lower in r.get('description', '').lower()]
                return results
            return {"error": resp.text}
        except Exception as e:
            return {"error": str(e)}

    def from_other(self, limit=20):
        """Get entries from the other Claude (not me)."""
        other = "G" if self.author == "R" else "R"
        return self.get(author=other, limit=limit)

    def since(self, timestamp):
        """Get entries created since a specific timestamp (efficient - only new data).

        Args:
            timestamp: ISO format string like '2025-12-12T05:00:00'

        Returns:
            List of entries created after that time
        """
        try:
            url = f"{self.base_url}?created_at=gt.{timestamp}&order=created_at.desc"
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            return {"error": resp.text}
        except Exception as e:
            return {"error": str(e)}

    def new_from_other(self, timestamp=None):
        """Get only NEW entries from the other Claude since last check.

        Args:
            timestamp: ISO format string, or None to use 1 hour ago

        Returns:
            List of new entries from the other Claude
        """
        other = "G" if self.author == "R" else "R"
        if timestamp is None:
            # Default: last hour
            from datetime import timedelta
            timestamp = (datetime.utcnow() - timedelta(hours=1)).isoformat()

        try:
            url = f"{self.base_url}?author=eq.{other}&created_at=gt.{timestamp}&order=created_at.desc"
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            return {"error": resp.text}
        except Exception as e:
            return {"error": str(e)}

    def count(self, author=None, type=None):
        """Get count of entries without fetching all data (efficient).

        Args:
            author: Filter by author (R or G), or None for all
            type: Filter by type (lesson, snippet, etc.), or None for all

        Returns:
            Integer count or error dict
        """
        try:
            # Use Supabase count header
            headers = self.headers.copy()
            headers["Prefer"] = "count=exact"
            headers["Range-Unit"] = "items"

            url = f"{self.base_url}?select=id"
            if author:
                url += f"&author=eq.{author}"
            if type:
                url += f"&type=eq.{type}"

            resp = requests.head(url, headers=headers, timeout=10)
            # Count is in Content-Range header: "0-N/TOTAL"
            content_range = resp.headers.get("Content-Range", "")
            if "/" in content_range:
                return int(content_range.split("/")[1])
            return {"error": "Could not get count"}
        except Exception as e:
            return {"error": str(e)}

    def mine(self, limit=20):
        """Get my own entries."""
        return self.get(author=self.author, limit=limit)

    def stats(self):
        """Get quick stats about the shared brain."""
        try:
            all_entries = self.recent(limit=1000)
            if isinstance(all_entries, dict) and "error" in all_entries:
                return all_entries

            r_count = len([e for e in all_entries if e.get('author') == 'R'])
            g_count = len([e for e in all_entries if e.get('author') == 'G'])
            types = {}
            for e in all_entries:
                t = e.get('type', 'unknown')
                types[t] = types.get(t, 0) + 1

            return {
                "total": len(all_entries),
                "from_R": r_count,
                "from_G": g_count,
                "by_type": types
            }
        except Exception as e:
            return {"error": str(e)}

    def sync(self, cache_file=None):
        """Sync all entries to local cache for offline access.

        Args:
            cache_file: Path to cache file (default: shared_brain_cache.json)

        Returns:
            Dict with sync status and entry count
        """
        import json
        from pathlib import Path

        if cache_file is None:
            cache_file = Path(__file__).parent / "shared_brain_cache.json"
        else:
            cache_file = Path(cache_file)

        try:
            # Fetch all entries
            all_entries = self.recent(limit=10000)
            if isinstance(all_entries, dict) and "error" in all_entries:
                return all_entries

            # Save to cache
            cache_data = {
                "synced_at": datetime.now().isoformat(),
                "count": len(all_entries),
                "entries": all_entries
            }
            cache_file.write_text(json.dumps(cache_data, indent=2), encoding='utf-8')

            print(f"Synced {len(all_entries)} entries to {cache_file}")
            return {"status": "synced", "count": len(all_entries), "file": str(cache_file)}

        except Exception as e:
            return {"error": str(e)}

    def load_cache(self, cache_file=None):
        """Load entries from local cache (for offline use).

        Returns:
            List of cached entries or error dict
        """
        import json
        from pathlib import Path

        if cache_file is None:
            cache_file = Path(__file__).parent / "shared_brain_cache.json"
        else:
            cache_file = Path(cache_file)

        try:
            if not cache_file.exists():
                return {"error": "No cache file - run brain.sync() first"}

            cache_data = json.loads(cache_file.read_text(encoding='utf-8'))
            print(f"Loaded {cache_data['count']} entries from cache (synced: {cache_data['synced_at']})")
            return cache_data['entries']

        except Exception as e:
            return {"error": str(e)}

    def search_cache(self, query, cache_file=None):
        """Search the local cache (works offline).

        Args:
            query: Text to search for in content/description

        Returns:
            List of matching entries
        """
        entries = self.load_cache(cache_file)
        if isinstance(entries, dict) and "error" in entries:
            return entries

        query_lower = query.lower()
        results = [e for e in entries if
                   query_lower in e.get('content', '').lower() or
                   query_lower in e.get('description', '').lower() or
                   any(query_lower in tag.lower() for tag in e.get('tags', []))]

        return results


# Singleton instance
brain = SharedBrain()


if __name__ == "__main__":
    # Quick test
    print("Testing Shared Brain connection...")
    stats = brain.stats()
    print(f"Stats: {stats}")

    # Test save
    result = brain.learn("Test lesson from shared_brain.py module test", tags=["test"])
    print(f"Save result: {result}")

    # Test read
    recent = brain.recent(5)
    print(f"Recent entries: {len(recent) if isinstance(recent, list) else recent}")
