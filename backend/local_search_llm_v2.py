import ollama
import requests
from bs4 import BeautifulSoup
import re
import time
import random
from fake_useragent import UserAgent
from rich.console import Console
from rich.panel import Panel
from halo import Halo

class OllamaSearchAgent:
    """
    An agent that uses an Ollama model to answer questions based on content
    scraped from a whitelisted set of URLs.
    """
    
    SOURCE_SELECTION_PROMPT = """/no_think
You are a URL selector. Output ONLY the numbers of the best matching websites, comma-separated.
No explanation. No extra text. Just numbers like: 1,3

Available websites:
{sites_list}
"""

    SYNTHESIS_PROMPT = """/no_think
You are an expert INDIAN LEGAL RESEARCHER. Today is {current_date}.
You answer questions strictly based on the legal content scraped from authoritative Indian legal sources.

ABSOLUTE RULES — breaking any of these is FORBIDDEN:
- NEVER say "I cannot provide real-time updates" or "my knowledge is limited to" or any similar phrase.
- NEVER reference your training data, training cutoff, or pre-trained knowledge.
- NEVER recommend external websites or sources not in the context.
- ONLY use information from the CONTEXT section below.
- When citing legal content, include: case name, court name, judgment date, and section/article if mentioned.
- If the context contains no relevant legal information, say: "No relevant legal information was found in the scraped sources."
- Organise your answer clearly: use headings for different cases or topics if multiple are present.

--- CONTEXT START ---
{context}
--- CONTEXT END ---

Using ONLY the above context, answer the legal question now. Be precise and cite sources from the context.
"""
    
    FOLLOW_UP_PHRASES = ["more details", "tell me more", "elaborate", "go on"]
    TAGS_TO_SCRAPE = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'article', 'div']
    TAGS_TO_REMOVE = ['script', 'style', 'nav', 'footer', 'header', 'aside']

    def _get_headers(self) -> dict:
        """Returns headers with a fresh random User-Agent for every request."""
        try:
            ua = UserAgent()
            user_agent = ua.random
        except Exception:
            # Fallback if fake-useragent DB is unavailable
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        return {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-IN,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'DNT': '1',
        }


    def __init__(self, whitelist_urls: list[str], model: str = 'llama3'):
        self.whitelist = whitelist_urls
        self.model = model
        self.client = ollama.Client()
        self.last_context = None
        self.last_source = None
        self.console = Console()
        self.console.print(f"[bold green]Agent initialized with model '{self.model}' and {len(self.whitelist)} whitelisted sites.[/bold green]")

    def _select_relevant_source(self, question: str) -> list[str]:
        """
        Select multiple relevant sources. Falls back to all sites if selection fails.
        """
        sites_list = "\n".join([f"{i+1}. {url}" for i, url in enumerate(self.whitelist)])
        system_prompt = self.SOURCE_SELECTION_PROMPT.format(sites_list=sites_list)

        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': question}
                ],
                options={'temperature': 0.0},
                think=False
            )
            
            content = response['message']['content'].strip()
            matches = re.findall(r'\d+', content)

            selected_urls = []
            for m in matches:
                idx = int(m) - 1
                if 0 <= idx < len(self.whitelist):
                    selected_urls.append(self.whitelist[idx])

            if not selected_urls:
                # Fallback: use all whitelisted sites so we always attempt scraping
                self.console.print(f"[yellow]Source selector returned no match — falling back to all {len(self.whitelist)} sites.[/yellow]")
                return list(self.whitelist)

            return list(set(selected_urls))  # dedupe

        except Exception as e:
            self.console.print(f"[bold red]Error during source selection: {e}[/bold red]")
            # On error, also fall back to all sites
            return list(self.whitelist)

    def _scrape_and_extract_text(self, url: str) -> str | None:
        """
        Scrapes the given URL with rotating User-Agent and human-like delays.
        """
        try:
            # Human-like delay: 2–5 seconds between requests to avoid bot detection
            delay = random.uniform(2, 5)
            self.console.print(f"   [dim]Waiting {delay:.1f}s before fetching {url}...[/dim]")
            time.sleep(delay)

            headers = self._get_headers()
            self.console.print(f"   [dim]User-Agent: {headers['User-Agent'][:60]}...[/dim]")

            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')

            for tag in soup(self.TAGS_TO_REMOVE):
                tag.decompose()

            text_chunks = [
                tag.get_text(separator=' ', strip=True)
                for tag in soup.find_all(self.TAGS_TO_SCRAPE)
                if tag.get_text(strip=True)
            ]
            
            full_text = ' '.join(text_chunks)
            return re.sub(r'\s+', ' ', full_text)

        except requests.RequestException as e:
            self.console.print(f"[bold red]Error fetching URL {url}: {e}[/bold red]")
            return None
        except Exception as e:
            self.console.print(f"[bold red]Error processing content from {url}: {e}[/bold red]")
            return None


    def _synthesize_answer(self, question: str, context: str) -> str:
        """
        Uses the LLM to generate an answer based on the question and the scraped context.
        """
        import datetime
        current_date = datetime.datetime.now().strftime("%B %d, %Y")
        system_prompt = self.SYNTHESIS_PROMPT.format(current_date=current_date, context=context)
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': question}
                ],
                options={'temperature': 0.1},
                think=False  # Disable qwen3 chain-of-thought that ignores system prompts
            )
            raw = response['message']['content']
            return self._clean_response(raw)
        except Exception as e:
            self.console.print(f"[bold red]Error during answer synthesis: {e}[/bold red]")
            return "An error occurred while generating the answer."

    def _clean_response(self, text: str) -> str:
        """
        Post-processing safety net: removes any paragraph where the model
        ignores the system prompt and talks about its training cutoff or
        recommends external news sources.
        """
        BAD_PHRASES = [
            "as of now, i can't",
            "as of now, i cannot",
            "i can't provide real-time",
            "i cannot provide real-time",
            "my knowledge is based on",
            "my knowledge cutoff",
            "data up to",
            "i recommend checking",
            "for the most accurate",
            "for the most up-to-date",
            "just let me know",
            "i can summarize a specific topic",
        ]
        paragraphs = text.split('\n')
        cleaned = []
        for para in paragraphs:
            lower = para.lower()
            if any(bad in lower for bad in BAD_PHRASES):
                continue  # Drop this line entirely
            cleaned.append(para)
        # Strip leading/trailing blank lines
        return '\n'.join(cleaned).strip()

    def query(self, question: str) -> dict:
        """
        Main method to handle a user's query through the full RAG pipeline.
        """
        results = {}
        source_urls = []

        # Follow-up handling
        if question.lower().strip() in self.FOLLOW_UP_PHRASES and self.last_context:
            self.console.print("[cyan]Detected follow-up question. Reusing last context...[/cyan]")
            results[self.last_source] = self._synthesize_answer(question, self.last_context)
            source_urls = [self.last_source]
        else:
            source_urls = self._select_relevant_source(question)
            if not source_urls:
                return {
                    "answers": {"system": "I could not determine relevant sources from the whitelist."},
                    "sources": None
                }

            self.console.print(f"   [dim]Sources selected: {', '.join(source_urls)}[/dim]")

            first_ctx = None
            for url in source_urls:
                ctx = self._scrape_and_extract_text(url)
                if ctx:
                    answer = self._synthesize_answer(question, ctx)
                    results[url] = answer
                    if first_ctx is None:  # capture first successful context for follow-ups
                        first_ctx = ctx

            if not results:
                return {
                    "answers": {"system": "I was unable to retrieve or process content from the selected sources."},
                    "sources": source_urls
                }

            # Store last context & source for follow-up (use the first one only)
            first_src = list(results.keys())[0]
            self.last_context = first_ctx
            self.last_source = first_src

        return {"answers": results, "sources": source_urls}


if __name__ == "__main__":
    console = Console()
    
    ALL_SITES = [
        "https://www.thehindu.com/news/national/",
        "https://timesofindia.indiatimes.com/india",
        "https://indianexpress.com/section/india/",
        "https://www.hindustantimes.com/india-news",
        "https://www.indiatoday.in/india",
        "https://www.firstpost.com/category/india",
        "https://thewire.in/category/politics/external-affairs"
    ]
    
    OLLAMA_MODEL = 'qwen3:4b-instruct'
    
    console.print(Panel("[bold yellow]Please select the websites to use for this session as a reference.[/bold yellow]"))
    for i, site in enumerate(ALL_SITES):
        console.print(f"  [cyan][{i+1}][/cyan] {site}")
    console.print("  [cyan][all][/cyan] Use all websites")

    while True:
        user_choice = input("Enter the numbers of the sites (e.g., 1,3,4) or 'all': ")
        selected_sites = []
        if user_choice.lower() == 'all':
            selected_sites = ALL_SITES
            break
        else:
            try:
                indices = [int(i.strip()) - 1 for i in user_choice.split(',')]
                if all(0 <= index < len(ALL_SITES) for index in indices):
                    selected_sites = [ALL_SITES[index] for index in indices]
                    break
                else:
                    console.print("[bold red]Invalid selection. One or more numbers are out of range.[/bold red]")
            except ValueError:
                console.print("[bold red]Invalid input. Please enter numbers separated by commas or 'all'.[/bold red]")

    if not selected_sites:
        console.print("[bold red]No valid websites selected. Exiting.[/bold red]")
        exit()

    agent = OllamaSearchAgent(whitelist_urls=selected_sites, model=OLLAMA_MODEL)

    console.print("\n[bold green]Local Search Agent is ready. Type 'exit' to quit.[/bold green]")
    while True:
        user_question = input("\nPlease ask a question: ")
        if user_question.lower() == 'exit':
            break
        
        spinner = Halo(text='Thinking...', spinner='dots')
        try:
            spinner.start()
            result = agent.query(user_question)
            spinner.succeed("Done!")
        except Exception as e:
            spinner.fail(f"An error occurred: {e}")
            continue

        # Display each answer separately like Google results
        for src, ans in result["answers"].items():
            answer_panel = Panel(
                ans,
                title="[bold green]Answer[/bold green]",
                subtitle=f"[dim]Source: {src}[/dim]",
                border_style="blue"
            )
            console.print(answer_panel)
