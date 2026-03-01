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
You are an expert at selecting the most relevant online resource.

Respond with ONLY the number of the most appropriate option. Do not provide any other text or explanation.

Here is the list of available websites:
{sites_list}
"""

    SYNTHESIS_PROMPT = """
You are a highly capable factual information extraction engine. 
Today's date is {current_date}.

Your task is to answer the user's question based *ONLY* on the provided context.
Follow these rules strictly:
1. DO NOT use any of your pre-trained knowledge.
2. DO NOT mention your knowledge cutoff date or say you cannot provide real-time updates. The context provided IS the real-time update.
3. ONLY use information present in the 'CONTEXT' section. If the answer isn't in the context, say "The provided context does not contain this information."
4. If the user asks a vague question like "tell me more" or "latest news", provide a detailed, well-structured summary of the context.
5. Extract key facts and direct quotes from the text to support your summary.

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

    def _select_relevant_source(self, question: str) -> str | None:
        
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
            
            ## Change: The logic is now much more robust. It looks for a number instead of a URL.
            # Find the first number in the response.
            match = re.search(r'\d+', content)
            if match:
                selected_index = int(match.group(0)) - 1
                if 0 <= selected_index < len(self.whitelist):
                    return self.whitelist[selected_index]
                else:
                    self.console.print(f"[bold red]Warning: LLM returned an invalid number: {selected_index + 1}[/bold red]")
                    return None
            else:
                self.console.print(f"[bold red]Warning: LLM did not return a valid number. Response: '{content}'[/bold red]")
                return None

        except Exception as e:
            self.console.print(f"[bold red]Error during source selection: {e}[/bold red]")
            return None

    def _scrape_and_extract_text(self, url: str) -> str | None:
        """
        Scrapes the given URL, removes clutter, and extracts clean text content.
        """
        try:
            response = requests.get(url, headers=self.REQUEST_HEADERS, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')

            ## Change: Added more common non-content tags to the removal list for cleaner text.
            for tag in soup(self.TAGS_TO_REMOVE):
                tag.decompose()

            text_chunks = [
                tag.get_text(separator=' ', strip=True)
                for tag in soup.find_all(self.TAGS_TO_SCRAPE)
                if tag.get_text(strip=True)
            ]
            
            full_text = ' '.join(text_chunks)
            # Normalize whitespace to a single space
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
                options={'temperature': 0.1} # A little creativity can help summarization
            )
            return response['message']['content']
        except Exception as e:
            self.console.print(f"[bold red]Error during answer synthesis: {e}[/bold red]")
            return "An error occurred while generating the answer."

    def query(self, question: str) -> dict:
        """
        Main method to handle a user's query through the full RAG pipeline.
        """
        context = None
        source_url = None
        
        # Check if it's a follow-up question
        if question.lower().strip() in self.FOLLOW_UP_PHRASES and self.last_context:
            self.console.print("[cyan]Detected follow-up question. Reusing last context...[/cyan]")
            context = self.last_context
            source_url = self.last_source
        else:
           
            source_url = self._select_relevant_source(question)

            if not source_url:
                return {
                    "answer": "I could not determine a relevant source from the whitelist to answer your question.",
                    "source": None
                }
            self.console.print(f"   [dim]Source selected: {source_url}[/dim]")

            context = self._scrape_and_extract_text(source_url)

            if not context:
                return {
                    "answer": f"I was unable to retrieve or process the content from {source_url}.",
                    "source": source_url
                }
            
            # Store for potential follow-ups
            self.last_context = context
            self.last_source = source_url

        answer = self._synthesize_answer(question, context)

        return {"answer": answer, "source": source_url}

if __name__ == "__main__":
    console = Console()
    
    ALL_SITES = [
        "https://www.thehindu.com/news/national/",
        "https://timesofindia.indiatimes.com/india",
        "https://indianexpress.com/section/india/",
        "https://www.hindustantimes.com/india-news",
        "https://www.ndtv.com/india",
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
        
        ## Change: Added a spinner for better user feedback during processing.
        spinner = Halo(text='Thinking...', spinner='dots')
        try:
            spinner.start()
            result = agent.query(user_question)
            spinner.succeed("Done!")
        except Exception as e:
            spinner.fail(f"An error occurred: {e}")
            continue

        ## Change: Used 'rich.panel' to format the final output beautifully.
        answer_panel = Panel(
            result["answer"],
            title="[bold green]Final Answer[/bold green]",
            subtitle=f"[dim]Source: {result['source']}[/dim]",
            border_style="blue"
        )
        console.print(answer_panel)