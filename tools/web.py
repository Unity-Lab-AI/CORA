"""
C.O.R.A Web Tools Module
Version: 2.2.0
Unity AI Lab

Web search, URL fetching, and content summarization.
"""

import requests
import re
from typing import Optional, Dict, List, Any
from urllib.parse import quote_plus, urlparse
from html.parser import HTMLParser


class HTMLTextExtractor(HTMLParser):
    """Extract text content from HTML."""

    def __init__(self):
        super().__init__()
        self.result = []
        self.skip_tags = {'script', 'style', 'head', 'meta', 'link'}
        self.current_tag = None

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag

    def handle_endtag(self, tag):
        self.current_tag = None

    def handle_data(self, data):
        if self.current_tag not in self.skip_tags:
            text = data.strip()
            if text:
                self.result.append(text)

    def get_text(self) -> str:
        return ' '.join(self.result)


def extract_text_from_html(html: str) -> str:
    """Extract readable text from HTML content."""
    parser = HTMLTextExtractor()
    try:
        parser.feed(html)
        return parser.get_text()
    except Exception:
        # Fallback: strip tags with regex
        clean = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        clean = re.sub(r'<style[^>]*>.*?</style>', '', clean, flags=re.DOTALL | re.IGNORECASE)
        clean = re.sub(r'<[^>]+>', ' ', clean)
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()


def instant_answer(query: str) -> Dict[str, Any]:
    """
    Get instant answer from DuckDuckGo API.

    This uses DDG's instant answer API which returns direct answers,
    summaries, and related topics - much faster than HTML scraping.

    Args:
        query: Search query string

    Returns:
        Dict with 'success', 'answer', 'abstract', 'related', etc.
    """
    if not query or not query.strip():
        return {'success': False, 'error': 'Empty query'}

    try:
        url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1"
        headers = {'User-Agent': 'CORA/2.3.0'}

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        result = {
            'success': True,
            'query': query,
            'answer': data.get('Answer', ''),
            'abstract': data.get('AbstractText', ''),
            'abstract_source': data.get('AbstractSource', ''),
            'abstract_url': data.get('AbstractURL', ''),
            'definition': data.get('Definition', ''),
            'definition_source': data.get('DefinitionSource', ''),
            'related': []
        }

        # Extract related topics
        for topic in data.get('RelatedTopics', [])[:5]:
            if isinstance(topic, dict) and topic.get('Text'):
                result['related'].append({
                    'text': topic['Text'][:200],
                    'url': topic.get('FirstURL', '')
                })

        # Check if we got any useful info
        has_content = any([
            result['answer'],
            result['abstract'],
            result['definition'],
            result['related']
        ])

        if not has_content:
            result['message'] = 'No instant answer available. Try web_search() for more results.'

        return result

    except requests.Timeout:
        return {'success': False, 'error': 'Request timed out'}
    except requests.RequestException as e:
        return {'success': False, 'error': f'Request failed: {e}'}
    except Exception as e:
        return {'success': False, 'error': f'Error: {e}'}


def web_search(query: str, num_results: int = 5) -> Dict[str, Any]:
    """
    Search the web using DuckDuckGo HTML API.

    Args:
        query: Search query string
        num_results: Maximum number of results to return

    Returns:
        Dict with 'success', 'results' list, and optional 'error'
    """
    if not query or not query.strip():
        return {
            'success': False,
            'error': 'Empty search query',
            'results': []
        }

    try:
        # DuckDuckGo HTML search
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        html = response.text
        results = []

        # Parse DuckDuckGo results
        # Look for result links and snippets
        result_pattern = r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>([^<]+)</a>'
        snippet_pattern = r'<a[^>]+class="result__snippet"[^>]*>([^<]+(?:<[^>]+>[^<]*</[^>]+>)*[^<]*)</a>'

        links = re.findall(result_pattern, html)
        snippets = re.findall(snippet_pattern, html)

        for i, (link, title) in enumerate(links[:num_results]):
            snippet = snippets[i] if i < len(snippets) else ''
            # Clean snippet of any remaining tags
            snippet = re.sub(r'<[^>]+>', '', snippet)

            results.append({
                'title': title.strip(),
                'url': link,
                'snippet': snippet.strip()
            })

        return {
            'success': True,
            'query': query,
            'results': results,
            'count': len(results)
        }

    except requests.Timeout:
        return {
            'success': False,
            'error': 'Search request timed out',
            'results': []
        }
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'Search request failed: {str(e)}',
            'results': []
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Search error: {str(e)}',
            'results': []
        }


def fetch_url(url: str, timeout: int = 15) -> Dict[str, Any]:
    """
    Fetch content from a URL.

    Args:
        url: The URL to fetch
        timeout: Request timeout in seconds

    Returns:
        Dict with 'success', 'content', 'content_type', and optional 'error'
    """
    if not url or not url.strip():
        return {
            'success': False,
            'error': 'Empty URL',
            'content': None
        }

    # Validate URL
    try:
        parsed = urlparse(url)
        if not parsed.scheme:
            url = 'https://' + url
        elif parsed.scheme not in ('http', 'https'):
            return {
                'success': False,
                'error': f'Unsupported URL scheme: {parsed.scheme}',
                'content': None
            }
    except Exception:
        return {
            'success': False,
            'error': 'Invalid URL format',
            'content': None
        }

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', 'text/html')

        return {
            'success': True,
            'url': url,
            'content': response.text,
            'content_type': content_type,
            'status_code': response.status_code,
            'length': len(response.text)
        }

    except requests.Timeout:
        return {
            'success': False,
            'error': f'Request timed out after {timeout}s',
            'content': None
        }
    except requests.HTTPError as e:
        return {
            'success': False,
            'error': f'HTTP error: {e.response.status_code}',
            'content': None
        }
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'Request failed: {str(e)}',
            'content': None
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Fetch error: {str(e)}',
            'content': None
        }


def summarize_url(url: str, max_length: int = 500) -> Dict[str, Any]:
    """
    Fetch a URL and summarize its text content.

    Args:
        url: The URL to fetch and summarize
        max_length: Maximum length of summary in characters

    Returns:
        Dict with 'success', 'summary', 'title', and optional 'error'
    """
    # Fetch the URL
    fetch_result = fetch_url(url)

    if not fetch_result['success']:
        return {
            'success': False,
            'error': fetch_result['error'],
            'summary': None
        }

    html = fetch_result['content']

    # Extract title
    title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else 'No title'

    # Extract main text
    text = extract_text_from_html(html)

    if not text:
        return {
            'success': True,
            'url': url,
            'title': title,
            'summary': 'No readable text content found.',
            'length': 0
        }

    # Create summary (first max_length chars, break at sentence)
    if len(text) <= max_length:
        summary = text
    else:
        summary = text[:max_length]
        # Try to break at sentence
        last_period = summary.rfind('.')
        last_question = summary.rfind('?')
        last_exclaim = summary.rfind('!')
        break_point = max(last_period, last_question, last_exclaim)

        if break_point > max_length // 2:
            summary = summary[:break_point + 1]
        else:
            summary = summary + '...'

    return {
        'success': True,
        'url': url,
        'title': title,
        'summary': summary,
        'full_length': len(text),
        'summary_length': len(summary)
    }


def search_and_summarize(query: str, num_results: int = 3) -> Dict[str, Any]:
    """
    Search the web and summarize top results.

    Args:
        query: Search query string
        num_results: Number of results to summarize

    Returns:
        Dict with 'success', 'results' list with summaries
    """
    search_result = web_search(query, num_results)

    if not search_result['success']:
        return search_result

    results_with_summaries = []

    for result in search_result['results']:
        url = result.get('url', '')
        if url:
            summary_result = summarize_url(url, max_length=300)
            result['summary'] = summary_result.get('summary', result.get('snippet', ''))
            result['full_content_available'] = summary_result.get('success', False)

        results_with_summaries.append(result)

    return {
        'success': True,
        'query': query,
        'results': results_with_summaries,
        'count': len(results_with_summaries)
    }


# Convenience functions for CLI integration
def search(query: str) -> str:
    """CLI-friendly search function."""
    result = web_search(query)

    if not result['success']:
        return f"Search failed: {result['error']}"

    if not result['results']:
        return f"No results found for: {query}"

    output = [f"Search results for: {query}\n"]

    for i, r in enumerate(result['results'], 1):
        output.append(f"{i}. {r['title']}")
        output.append(f"   {r['url']}")
        if r.get('snippet'):
            output.append(f"   {r['snippet'][:150]}...")
        output.append("")

    return '\n'.join(output)


def fetch(url: str) -> str:
    """CLI-friendly fetch function."""
    result = fetch_url(url)

    if not result['success']:
        return f"Fetch failed: {result['error']}"

    text = extract_text_from_html(result['content'])

    if len(text) > 2000:
        text = text[:2000] + '...\n[Content truncated]'

    return f"Content from {url}:\n\n{text}"


def summarize(url: str) -> str:
    """CLI-friendly summarize function."""
    result = summarize_url(url)

    if not result['success']:
        return f"Summarize failed: {result['error']}"

    return f"Title: {result['title']}\nURL: {url}\n\nSummary:\n{result['summary']}"


# Module test
if __name__ == '__main__':
    print("Testing web.py module...")

    # Test search
    print("\n--- Web Search Test ---")
    result = web_search("Python programming", num_results=3)
    print(f"Success: {result['success']}")
    print(f"Results: {result.get('count', 0)}")

    # Test fetch
    print("\n--- URL Fetch Test ---")
    result = fetch_url("https://example.com")
    print(f"Success: {result['success']}")
    print(f"Length: {result.get('length', 0)}")

    # Test summarize
    print("\n--- URL Summarize Test ---")
    result = summarize_url("https://example.com")
    print(f"Success: {result['success']}")
    print(f"Title: {result.get('title', 'N/A')}")

    print("\nAll tests completed.")
