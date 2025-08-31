import ollama
import requests
from bs4 import BeautifulSoup
import re
from rich.console import Console
from rich.panel import Panel
from halo import Halo

class OllamaSearchAgent:
    """
    An agent that uses an Ollama model to answer questions based on content
    scraped from a whitelisted set of URLs.
    """
    
    SOURCE_SELECTION_PROMPT = """
You are an expert at selecting the most relevant online resources.

Respond with ONLY the numbers of the most appropriate options, separated by commas.
Do not provide any other text or explanation.

Here is the list of available websites:
{sites_list}
"""

    SYNTHESIS_PROMPT = """
You are a factual information extraction engine. Your task is to answer the user's question based *only* on the provided context.
Follow these rules strictly:
1. DO NOT use any of your own knowledge.
2. ONLY use information present in the 'CONTEXT' section.
3. If the user asks a vague question like "tell me more", provide a more detailed summary of the context.
4. Extract key facts and direct quotes from the text to support your summary.

--- CONTEXT ---
{context}
--- END CONTEXT ---
"""
    
    FOLLOW_UP_PHRASES = ["more details", "tell me more", "elaborate", "go on"]
    REQUEST_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    TAGS_TO_SCRAPE = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'article', 'div']
    TAGS_TO_REMOVE = ['script', 'style', 'nav', 'footer', 'header', 'aside']


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
        Select multiple relevant sources instead of just one.
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
                options={'temperature': 0.0}
            )
            
            content = response['message']['content'].strip()
            matches = re.findall(r'\d+', content)

            selected_urls = []
            for m in matches:
                idx = int(m) - 1
                if 0 <= idx < len(self.whitelist):
                    selected_urls.append(self.whitelist[idx])

            if not selected_urls:
                self.console.print(f"[bold red]Warning: LLM did not return valid numbers. Response: '{content}'[/bold red]")
                return []

            return list(set(selected_urls))  # dedupe

        except Exception as e:
            self.console.print(f"[bold red]Error during source selection: {e}[/bold red]")
            return []

    def _scrape_and_extract_text(self, url: str) -> str | None:
        """
        Scrapes the given URL, removes clutter, and extracts clean text content.
        """
        try:
            response = requests.get(url, headers=self.REQUEST_HEADERS, timeout=10)
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
        system_prompt = self.SYNTHESIS_PROMPT.format(context=context)
        try:
            response = self.client.chat(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': question}
                ],
                options={'temperature': 0.1}
            )
            return response['message']['content']
        except Exception as e:
            self.console.print(f"[bold red]Error during answer synthesis: {e}[/bold red]")
            return "An error occurred while generating the answer."

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

            for url in source_urls:
                ctx = self._scrape_and_extract_text(url)
                if ctx:
                    answer = self._synthesize_answer(question, ctx)
                    results[url] = answer

            if not results:
                return {
                    "answers": {"system": "I was unable to retrieve or process content from the selected sources."},
                    "sources": source_urls
                }

            # Store last context & source for follow-up (use the first one only)
            first_src = list(results.keys())[0]
            self.last_context = ctx
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
    
    OLLAMA_MODEL = 'gemma3:12b' 
    
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
