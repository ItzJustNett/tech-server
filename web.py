import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import nltk
from nltk.tokenize import sent_tokenize
from transformers import pipeline
import time
import re

class WebSearchAI:
    def __init__(self):
        self.search_engine = DDGS()
        print("Initializing summarization pipeline...")
        self.summarizer = pipeline("summarization", device="cpu")
        # Download necessary NLTK data if not already present
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            print("Downloading NLTK punkt tokenizer...")
            nltk.download('punkt')
    
    def search(self, query, num_results=5):
        """Search DuckDuckGo and return results"""
        try:
            print(f"Searching for: {query}")
            results = self.search_engine.text(query, max_results=num_results * 2)  # Get more results to compensate for filtering
            # Convert results to list for easier handling
            results_list = list(results)
            print(f"Found {len(results_list)} search results")
            
            # Filter out Russian results
            filtered_results = self.filter_russian_results(results_list)
            print(f"After filtering Russian results: {len(filtered_results)} results remaining")
            
            # Return only the requested number of results
            return filtered_results[:num_results]
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def filter_russian_results(self, results):
        """Filter out Russian websites and content"""
        filtered = []
        
        for result in results:
            # Skip if no URL
            if 'href' not in result:
                continue
                
            url = result['href'].lower()
            
            # Check for Russian domain
            if url.endswith('.ru') or '.ru/' in url:
                print(f"Filtering out Russian domain: {url}")
                continue
            
            # Check for other common Russian domains
            russian_domains = ['.рф', '.su', 'russia', 'russian', 'moskva', 'moscow.', '.yandex.']
            if any(domain in url for domain in russian_domains):
                print(f"Filtering out likely Russian site: {url}")
                continue
            
            # Basic content analysis for Russian language detection in title or snippet
            title = result.get('title', '').lower()
            snippet = result.get('body', '') or result.get('snippet', '') or result.get('description', '')
            
            # Check for Cyrillic characters (a simple approach)
            cyrillic_pattern = re.compile(r'[а-яА-Я]')
            if cyrillic_pattern.search(title) or cyrillic_pattern.search(snippet):
                print(f"Filtering out result with Cyrillic text: {url}")
                continue
                
            filtered.append(result)
            
        return filtered
    
    def analyze_search_results(self, results, query):
        """Determine which results are most promising to explore"""
        if not results:
            print("No search results to analyze")
            return []
            
        print("Analyzing search results for relevance...")
        scored_results = []
        
        for result in results:
            score = 1  # Base score
            
            # Check if query terms appear in title
            if 'title' in result:
                for term in query.lower().split():
                    if term in result['title'].lower():
                        score += 2
            
            # Check if query terms appear in body/snippet/description
            content_field = None
            for field in ['body', 'snippet', 'content', 'description']:
                if field in result and result[field]:
                    content_field = field
                    break
                    
            if content_field:
                for term in query.lower().split():
                    if term in result[content_field].lower():
                        score += 1
            
            # Add more score if the URL seems authoritative
            if 'href' in result:
                url = result['href'].lower()
                if '.gov' in url or '.edu' in url:
                    score += 3
                if 'weather' in url and 'arizona' in url:  # Example of query-specific boosting
                    score += 5
            
            scored_results.append((score, result))
        
        # Sort by score and get top results
        best_results = [r[1] for r in sorted(scored_results, key=lambda x: x[0], reverse=True)[:3]]
        print(f"Selected {len(best_results)} most relevant results")
        return best_results
    
    def fetch_content(self, url):
        """Fetch and parse webpage content"""
        try:
            print(f"Fetching content from: {url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"Failed to fetch {url}: Status code {response.status_code}")
                return ""
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for Russian content
            if self.is_russian_content(soup, url):
                print(f"Filtering out Russian content page: {url}")
                return ""
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.extract()
            
            # Extract main content - more sophisticated than before
            main_content = None
            
            # Try to find main content container
            for container in ['main', 'article', '#content', '.content', '#main', '.main']:
                main = soup.select(container)
                if main:
                    main_content = main[0]
                    break
            
            # If no main container found, use body
            if not main_content:
                main_content = soup.body
            
            if not main_content:
                return ""
            
            # Get all paragraphs from main content
            paragraphs = main_content.find_all('p')
            content = ' '.join([p.get_text().strip() for p in paragraphs])
            
            # If we couldn't find paragraphs, try getting all text
            if not content and main_content:
                content = main_content.get_text(separator=' ', strip=True)
            
            print(f"Extracted {len(content)} characters of content")
            return content
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return ""
    
    def is_russian_content(self, soup, url):
        """Detect if a page contains primarily Russian content"""
        # Check for Cyrillic letters in the main text
        text = soup.get_text()
        
        # Check meta language
        lang_tags = soup.select('html[lang], meta[http-equiv="Content-Language"]')
        for tag in lang_tags:
            lang = tag.get('lang') or tag.get('content', '')
            if lang and ('ru' in lang.lower() or 'ru-' in lang.lower()):
                return True
        
        # Count Cyrillic characters
        cyrillic_count = len(re.findall(r'[а-яА-Я]', text))
        total_chars = len(text)
        
        # If more than 15% of characters are Cyrillic, consider it Russian
        if total_chars > 0 and (cyrillic_count / total_chars) > 0.15:
            return True
            
        return False
    
    def analyze_content(self, content, query):
        """Extract relevant information from the content"""
        if not content:
            return ""
            
        print("Analyzing content...")
        try:
            # Split into sentences
            sentences = sent_tokenize(content)
            
            # Score sentences by relevance to query
            query_terms = query.lower().split()
            relevant_sentences = []
            
            for sentence in sentences:
                sentence_lower = sentence.lower()
                matches = sum(1 for term in query_terms if term in sentence_lower)
                if matches > 0:
                    relevant_sentences.append((matches, sentence))
            
            # Sort by relevance score
            relevant_sentences.sort(reverse=True, key=lambda x: x[0])
            
            # Take top sentences (max 15)
            top_sentences = [s[1] for s in relevant_sentences[:15]]
            
            if not top_sentences:
                # If no relevant sentences found, take first few sentences
                top_sentences = sentences[:5]
            
            combined_text = ' '.join(top_sentences)
            
            # Summarize if we have too much content
            if len(combined_text) > 1000:
                print("Summarizing content...")
                try:
                    summary = self.summarizer(combined_text, 
                                            max_length=300, 
                                            min_length=100, 
                                            do_sample=False)
                    return summary[0]['summary_text']
                except Exception as e:
                    print(f"Summarization error: {e}")
                    # Fall back to returning truncated content
                    return combined_text[:1000] + "..."
            
            return combined_text
        except Exception as e:
            print(f"Content analysis error: {e}")
            # Return truncated content as fallback
            return content[:500] + "..."
    
    def answer_query(self, query):
        """Main function to answer a user query"""
        # 1. Search
        search_results = self.search(query)
        
        if not search_results:
            return "I'm sorry, I couldn't find any information about that. Please try a different query."
        
        # 2. Analyze search results
        best_results = self.analyze_search_results(search_results, query)
        
        if not best_results:
            return "I found some results, but couldn't determine which ones would be most helpful. Please try a more specific query."
        
        # 3. Fetch content from best results
        all_content = []
        for result in best_results:
            if 'href' in result:
                content = self.fetch_content(result['href'])
                if content:
                    analyzed = self.analyze_content(content, query)
                    all_content.append({
                        'source': result['href'],
                        'title': result.get('title', 'Unknown Title'),
                        'content': analyzed
                    })
            
            # Small delay to avoid overloading servers
            time.sleep(1)
        
        # 4. Synthesize information
        if not all_content:
            return "I found some potentially relevant websites, but couldn't extract useful information from them. Please try a different query."
            
        return self.synthesize_answer(query, all_content)
    
    def synthesize_answer(self, query, content_list):
        """Generate a final answer based on collected information"""
        if not content_list:
            return "I couldn't find specific information about that topic."
            
        answer = f"Here's what I found about '{query}':\n\n"
        
        for i, item in enumerate(content_list, 1):
            answer += f"Source {i}: {item['title']}\n"
            answer += f"{item['content']}\n\n"
            answer += f"URL: {item['source']}\n\n"
            
        answer += "This information was compiled from web search results."
        return answer

# Usage
if __name__ == "__main__":
    ai = WebSearchAI()
    query = input("What would you like to know? ")
    answer = ai.answer_query(query)
    print("\nANSWER:")
    print("-" * 80)
    print(answer)
    print("-" * 80)