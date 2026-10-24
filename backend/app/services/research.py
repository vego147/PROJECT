from datetime import datetime, timezone
from urllib.parse import quote_plus
import asyncio, re
import httpx
from html.parser import HTMLParser
from ..config import settings

DEMO_SOURCES = [
    {"title": "Reuters: Latest news and reporting", "url": "https://www.reuters.com/", "published_date": None, "snippet": "Reference source only. Demo mode did not fetch this page.", "credibility": "Reference only"},
    {"title": "Associated Press News", "url": "https://apnews.com/", "published_date": None, "snippet": "Reference source only. Demo mode did not fetch this page.", "credibility": "Reference only"},
]

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]; self.skip=0
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style','nav','header','footer','aside','noscript','svg'): self.skip += 1
        if tag in ('p','h1','h2','h3','article','section','br','li') and not self.skip: self.parts.append('\n')
    def handle_endtag(self, tag):
        if tag in ('script','style','nav','header','footer','aside','noscript','svg') and self.skip: self.skip -= 1
    def handle_data(self, data):
        if not self.skip:
            text = re.sub(r'\s+', ' ', data).strip()
            if text: self.parts.append(text)

def extract_html(html: str) -> str:
    parser=TextExtractor()
    try: parser.feed(html)
    except Exception: return ''
    text=re.sub(r'\n\s*\n+', '\n', '\n'.join(parser.parts))
    return text[:12000]

async def _fetch_page(client, source):
    url=source.get('url','')
    if not url.startswith(('http://','https://')): return source
    try:
        r=await client.get(url, follow_redirects=True, timeout=12, headers={'User-Agent':'Mozilla/5.0 (compatible; MarketingContentEngine/1.0)'})
        ctype=r.headers.get('content-type','')
        if r.status_code == 200 and 'text/html' in ctype:
            text=extract_html(r.text)
            if len(text)>300: return {**source, 'extracted_content':text, 'extraction_status':'extracted', 'http_status':r.status_code}
        return {**source, 'extracted_content':source.get('snippet',''), 'extraction_status':f'page returned {r.status_code} or non-HTML'}
    except Exception as e:
        return {**source, 'extracted_content':source.get('snippet',''), 'extraction_status':f'fetch failed: {type(e).__name__}'}

async def research_topic(topic: str) -> tuple[list[dict], str, list[dict]]:
    stages=[]
    if settings.tavily_api_key:
        try:
            from tavily import TavilyClient
            result=await asyncio.to_thread(lambda: TavilyClient(api_key=settings.tavily_api_key).search(query=topic, topic='general', max_results=5, include_answer=False))
            sources=[]
            for item in result.get('results',[]):
                sources.append({'title':item.get('title') or 'Untitled source','url':item.get('url') or '', 'published_date':item.get('published_date'), 'snippet':(item.get('content') or '')[:1200], 'credibility':'Search result; assess before publishing'})
            if sources:
                stages.append({'name':'Tavily search','status':'completed','detail':f'Found {len(sources)} search results.'})
                async with httpx.AsyncClient() as client:
                    # Fetch the best three results, not every URL returned by search.
                    extracted=await asyncio.gather(*[_fetch_page(client,s) for s in sources[:3]])
                sources=extracted + sources[3:]
                count=sum(1 for s in sources if s.get('extraction_status')=='extracted')
                stages.append({'name':'Top-article extraction','status':'completed' if count else 'warning','detail':f'Fetched readable article text from {count} of the top {min(3,len(sources))} URLs. Sites may block automated access.'})
                return sources,'tavily',stages
        except Exception as e:
            stages.append({'name':'Tavily search','status':'failed','detail':f'Search failed: {type(e).__name__}'})
    q=quote_plus(topic)
    sources=[{**s,'extracted_content':s['snippet'],'extraction_status':'not fetched'} for s in DEMO_SOURCES]
    sources.append({'title':f'Google search results for "{topic}"','url':f'https://www.google.com/search?q={q}','published_date':None,'snippet':'Demo mode did not search or extract this page.','extracted_content':'','extraction_status':'not fetched','credibility':'Search link; not verified'})
    stages.extend([{'name':'Web research','status':'warning','detail':'TAVILY_API_KEY is missing or search failed; no live research was performed.'},{'name':'Top-article extraction','status':'warning','detail':'No article pages were fetched in demo mode.'}])
    return sources,'demo',stages
