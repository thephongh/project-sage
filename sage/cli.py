"""Command-line interface for Project Sage."""

import sys
import json
from pathlib import Path
from typing import Optional
import typer
from rich import print
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel
from datetime import datetime

from sage.config import ConfigManager, SageConfig
from sage.setup_gui import SetupWindow
from sage.file_processor import FileProcessor
from sage.vector_store import VectorStore
from sage.llm_client import LLMClient
from sage.model_manager import ModelManager

app = typer.Typer(
    name="sage",
    help="Project Sage - An intelligent AI assistant for complex project management",
    add_completion=False
)
console = Console()


@app.command()
def setup():
    """Launch GUI to initialize Sage for this project."""
    project_path = Path.cwd()
    config_manager = ConfigManager(project_path)
    
    if config_manager.exists():
        if not typer.confirm("Configuration already exists. Do you want to reconfigure?"):
            return
            
    console.print("[bold blue]Launching setup window...[/bold blue]")
    
    try:
        setup_window = SetupWindow(project_path)
        config = setup_window.run()
        
        if config:
            console.print("[bold green]✓ Project initialized successfully![/bold green]")
            console.print(f"Configuration saved to: {config_manager.config_path}")
        else:
            console.print("[yellow]Setup cancelled.[/yellow]")
            
    except Exception as e:
        console.print(f"[bold red]Error during setup: {str(e)}[/bold red]")
        raise typer.Exit(1)


@app.command()
def update(force: bool = typer.Option(False, "--force", "-f", help="Force full re-scan of all files")):
    """Scan and index project documents."""
    project_path = Path.cwd()
    config_manager = ConfigManager(project_path)
    
    # Load configuration
    config = config_manager.load()
    if not config:
        console.print("[bold red]Project not initialized. Run 'sage setup' first.[/bold red]")
        raise typer.Exit(1)
        
    console.print("[bold blue]Updating knowledge base...[/bold blue]")
    
    # Initialize components
    processor = FileProcessor(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
        ocr_language=config.document_language
    )
    vector_store = VectorStore(config)
    vector_store.initialize()
    
    # Find files to process
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Scanning for files...", total=None)
        files_to_process = processor.find_files(project_path, force)
        progress.update(task, completed=100)
        
    if not files_to_process:
        console.print("[green]✓ Knowledge base is up to date.[/green]")
        return
        
    console.print(f"Found [bold]{len(files_to_process)}[/bold] files to process")
    
    # Clear vector store if force update
    if force:
        vector_store.clear()
        
    # Process files
    total_documents = 0
    failed_files = []
    
    with Progress() as progress:
        task = progress.add_task("Processing files...", total=len(files_to_process))
        
        for file_path in files_to_process:
            progress.update(task, description=f"Processing {file_path.name}...")
            
            try:
                documents = processor.process_file(file_path)
                if documents:
                    vector_store.add_documents(documents)
                    processor.update_metadata(project_path, file_path, documents)
                    total_documents += len(documents)
                else:
                    failed_files.append(file_path)
                    
            except Exception as e:
                console.print(f"[red]Error processing {file_path.name}: {str(e)}[/red]")
                failed_files.append(file_path)
                
            progress.update(task, advance=1)
            
    # Print summary
    console.print("\n[bold]Update Summary:[/bold]")
    console.print(f"  Files processed: {len(files_to_process) - len(failed_files)}")
    console.print(f"  Documents created: {total_documents}")
    if failed_files:
        console.print(f"  [red]Failed files: {len(failed_files)}[/red]")
        for f in failed_files[:5]:
            console.print(f"    - {f.name}")
        if len(failed_files) > 5:
            console.print(f"    ... and {len(failed_files) - 5} more")
            
    console.print("[bold green]✓ Knowledge base updated successfully![/bold green]")


@app.command()
def ask(query: str = typer.Argument(..., help="Your question about the project")):
    """Ask a question about your project documents."""
    project_path = Path.cwd()
    config_manager = ConfigManager(project_path)
    
    # Load configuration
    config = config_manager.load()
    if not config:
        console.print("[bold red]Project not initialized. Run 'sage setup' first.[/bold red]")
        raise typer.Exit(1)
        
    # Initialize components
    vector_store = VectorStore(config)
    vector_store.initialize()
    
    # Check if knowledge base exists
    doc_count = vector_store.get_document_count()
    if doc_count == 0:
        console.print("[bold yellow]Knowledge base is empty. Run 'sage update' first.[/bold yellow]")
        raise typer.Exit(1)
        
    # Search for relevant documents
    with console.status("[bold blue]Searching knowledge base...[/bold blue]"):
        documents = vector_store.search(query, k=5)
        
    if not documents:
        console.print("[yellow]No relevant documents found for your query.[/yellow]")
        return
        
    # Get answer from LLM
    with console.status("[bold blue]Generating answer...[/bold blue]"):
        llm_client = LLMClient(config)
        result = llm_client.answer_question(query, documents)
        
    # Display answer
    answer_panel = Panel(
        result['answer'],
        title="[bold]Answer[/bold]",
        border_style="blue"
    )
    console.print(answer_panel)
    
    # Display sources
    if result['sources']:
        console.print("\n[bold]Sources:[/bold]")
        for source in result['sources']:
            # Make path relative to project
            try:
                rel_path = Path(source).relative_to(project_path)
                console.print(f"  • {rel_path}")
            except:
                console.print(f"  • {source}")
                
    if result.get('error'):
        console.print("\n[bold red]Note: There was an error generating the answer. Please check your API key and connection.[/bold red]")


@app.command()
def status():
    """Show the status of the Sage knowledge base."""
    project_path = Path.cwd()
    config_manager = ConfigManager(project_path)
    
    # Load configuration
    config = config_manager.load()
    if not config:
        console.print("[bold red]Project not initialized. Run 'sage setup' first.[/bold red]")
        raise typer.Exit(1)
        
    # Get vector store info
    vector_store = VectorStore(config)
    vector_store.initialize()
    doc_count = vector_store.get_document_count()
    
    # Get file metadata
    processor = FileProcessor()
    metadata = processor.load_metadata(project_path)
    
    # Create status table
    table = Table(title="Project Sage Status", show_header=False)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Project Path", str(project_path))
    table.add_row("LLM Provider", config.llm_provider.title())
    table.add_row("LLM Model", config.llm_model)
    table.add_row("Document Language", config.document_language.upper())
    table.add_row("Files Indexed", str(len(metadata)))
    table.add_row("Total Chunks", str(doc_count))
    
    # Find last update time
    if metadata:
        last_update = max(
            datetime.fromisoformat(m['processed_at']) 
            for m in metadata.values()
        )
        table.add_row("Last Update", last_update.strftime("%Y-%m-%d %H:%M:%S"))
    else:
        table.add_row("Last Update", "Never")
        
    console.print(table)
    
    if doc_count == 0:
        console.print("\n[yellow]Knowledge base is empty. Run 'sage update' to index your documents.[/yellow]")


@app.command()
def gui():
    """Launch the enhanced GUI application."""
    project_path = Path.cwd()
    config_manager = ConfigManager(project_path)
    
    console.print("[bold blue]Launching Sage GUI...[/bold blue]")
    
    try:
        from sage.gui_app import SageGUI
        app = SageGUI(project_path)
        app.run()
    except ImportError as e:
        console.print(f"[bold red]Error: Missing GUI dependencies: {str(e)}[/bold red]")
        console.print("Install GUI dependencies with: pip install matplotlib")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Error launching GUI: {str(e)}[/bold red]")
        raise typer.Exit(1)


@app.command()
def chat():
    """Start an interactive chat session with your project documents."""
    project_path = Path.cwd()
    config_manager = ConfigManager(project_path)
    
    # Load configuration
    config = config_manager.load()
    if not config:
        console.print("[bold red]Project not initialized. Run 'sage setup' first.[/bold red]")
        raise typer.Exit(1)
        
    # Initialize components
    vector_store = VectorStore(config)
    vector_store.initialize()
    
    # Check if knowledge base exists
    doc_count = vector_store.get_document_count()
    if doc_count == 0:
        console.print("[bold yellow]Knowledge base is empty. Run 'sage update' first.[/bold yellow]")
        raise typer.Exit(1)
        
    # Initialize model manager for dynamic switching
    model_manager = ModelManager(config)
    
    # Start chat session
    current_provider, current_model = model_manager.get_current_model_info()
    console.print(Panel.fit(
        f"[bold blue]🤖 Sage Interactive Chat[/bold blue]\n\n"
        f"Project: {project_path.name}\n"
        f"Documents: {doc_count} chunks indexed\n"
        f"LLM: {current_provider.title()} {current_model}\n"
        f"Configured Providers: {', '.join(model_manager.get_configured_providers())}\n\n"
        f"[dim]Type your questions or 'exit' to quit\n"
        f"Commands: /help, /status, /model, /switch[/dim]",
        title="Chat Session Started",
        border_style="blue"
    ))
    
    conversation_history = []
    
    try:
        while True:
            # Get user input
            try:
                question = typer.prompt("\n🧑 You", prompt_suffix="")
            except (KeyboardInterrupt, EOFError):
                break
                
            # Handle special commands
            if question.lower().strip() in ['exit', 'quit', 'bye']:
                break
            elif question.strip().startswith('/'):
                _handle_chat_command(question.strip(), conversation_history, vector_store, config, model_manager)
                continue
            elif not question.strip():
                continue
                
            # Process the question
            current_provider, current_model = model_manager.get_current_model_info()
            with console.status(f"[bold blue]🤖 {current_provider.title()} {current_model} is thinking...[/bold blue]"):
                try:
                    # Search for relevant documents
                    documents = vector_store.search(question, k=5)
                    
                    if not documents:
                        console.print("[yellow]No relevant documents found for your question.[/yellow]")
                        continue
                        
                    # Get LLM client for current model
                    llm_client = model_manager.get_llm_client()
                    
                    # Get answer from LLM
                    result = llm_client.answer_question(question, documents)
                    
                    if result.get('error'):
                        console.print(f"[bold red]Error: {result['answer']}[/bold red]")
                        continue
                        
                    # Display answer
                    answer_panel = Panel(
                        result['answer'],
                        title="[bold]🤖 Sage[/bold]",
                        border_style="green"
                    )
                    console.print(answer_panel)
                    
                    # Display sources (compact format)
                    if result['sources']:
                        sources_text = "📚 " + ", ".join([
                            Path(source).relative_to(project_path).name 
                            for source in result['sources']
                        ])
                        console.print(f"[dim]{sources_text}[/dim]")
                        
                    # Add to conversation history
                    conversation_history.append({
                        'question': question,
                        'answer': result['answer'],
                        'sources': result['sources'],
                        'timestamp': datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    console.print(f"[bold red]Error: {str(e)}[/bold red]")
                    console.print("[dim]Check your API key and internet connection[/dim]")
                    
    except KeyboardInterrupt:
        pass
        
    # End chat session
    console.print(f"\n[bold blue]Chat session ended. Asked {len(conversation_history)} questions.[/bold blue]")
    if conversation_history:
        save_chat = typer.confirm("Save conversation history?")
        if save_chat:
            _save_chat_history(project_path, conversation_history)


def _handle_chat_command(command: str, history: list, vector_store: VectorStore, config: SageConfig, model_manager: ModelManager = None):
    """Handle special chat commands."""
    cmd = command.lower().strip()
    
    if cmd == '/help':
        help_text = """[bold]Available Commands:[/bold]
        
🔹 /help     - Show this help message
🔹 /status   - Show knowledge base status  
🔹 /model    - Show current model and available options
🔹 /switch   - Switch to a different LLM model
🔹 /clear    - Clear conversation history
🔹 /history  - Show conversation history
🔹 /sources  - List all indexed documents
🔹 exit      - End chat session

[bold]Model Switching:[/bold]
• /model - See current model and recommendations
• /switch google gemini-2.0-flash - Switch to specific model
• /switch ollama llama3.1:8b - Switch to local Ollama model
• You can switch models mid-conversation!

[bold]Tips:[/bold]
• Ask specific questions about your project documents
• Switch models for different tasks (fast vs. quality)
• Use follow-up questions to dive deeper into topics"""
        
        console.print(Panel(help_text, title="Chat Help", border_style="yellow"))
        
    elif cmd == '/status':
        doc_count = vector_store.get_document_count()
        status_text = f"""[bold]Knowledge Base Status:[/bold]

📊 Documents: {doc_count} chunks indexed
🤖 LLM: {config.llm_provider.title()} {config.llm_model}  
📝 Language: {config.document_language.upper()}
💬 Questions Asked: {len(history)}"""
        
        console.print(Panel(status_text, title="Status", border_style="cyan"))
        
    elif cmd == '/clear':
        history.clear()
        console.print("[yellow]Conversation history cleared.[/yellow]")
        
    elif cmd == '/history':
        if not history:
            console.print("[yellow]No conversation history yet.[/yellow]")
            return
            
        console.print(f"[bold]Conversation History ({len(history)} questions):[/bold]\n")
        for i, item in enumerate(history[-5:], 1):  # Show last 5
            console.print(f"[cyan]{i}. Q:[/cyan] {item['question'][:100]}...")
            console.print(f"[green]   A:[/green] {item['answer'][:150]}...\n")
            
    elif cmd == '/sources':
        # Get unique sources from conversation
        all_sources = set()
        for item in history:
            all_sources.update(item.get('sources', []))
            
        if all_sources:
            console.print("[bold]Documents referenced in conversation:[/bold]")
            for source in sorted(all_sources):
                try:
                    rel_path = Path(source).relative_to(Path.cwd())
                    console.print(f"📄 {rel_path}")
                except:
                    console.print(f"📄 {source}")
        else:
            console.print("[yellow]No sources referenced yet.[/yellow]")
            
    elif cmd == '/model':
        if not model_manager:
            console.print("[red]Model manager not available[/red]")
            return
            
        current_provider, current_model = model_manager.get_current_model_info()
        configured_providers = model_manager.get_configured_providers()
        recommendations = model_manager.get_recommended_models()
        
        model_text = f"""[bold]Current Model:[/bold]
🤖 {current_provider.title()} {current_model}
{model_manager.get_model_description(current_provider, current_model)}

[bold]Configured Providers:[/bold]
{', '.join([p.title() for p in configured_providers])}

[bold]Recommended Models:[/bold]"""

        for use_case, (provider, model) in recommendations.items():
            model_text += f"\n• {use_case.title()}: {provider} {model}"
            
        model_text += f"""

[bold]Usage:[/bold]
• /switch {current_provider} {current_model} - Stay with current
• /switch google gemini-2.0-flash - Switch to fast model
• /switch ollama llama3.1:8b - Switch to local model"""
        
        console.print(Panel(model_text, title="Model Information", border_style="blue"))
        
    elif cmd.startswith('/switch'):
        if not model_manager:
            console.print("[red]Model manager not available[/red]")
            return
            
        # Parse switch command: /switch provider model
        parts = command.split()
        if len(parts) != 3:
            console.print("[red]Usage: /switch <provider> <model>[/red]")
            console.print("[dim]Example: /switch google gemini-2.0-flash[/dim]")
            return
            
        _, provider, model = parts
        
        # Attempt to switch
        if model_manager.switch_model(provider, model):
            description = model_manager.get_model_description(provider, model)
            console.print(f"[green]✓ Switched to {provider.title()} {model}[/green]")
            console.print(f"[dim]{description}[/dim]")
        else:
            console.print(f"[red]Failed to switch to {provider} {model}[/red]")
            console.print("[dim]Check provider name, model name, and API key configuration[/dim]")
            
    else:
        console.print(f"[red]Unknown command: {command}[/red]")
        console.print("[dim]Type '/help' for available commands[/dim]")


def _save_chat_history(project_path: Path, history: list):
    """Save conversation history to file."""
    try:
        chat_dir = project_path / ".sage" / "chats"
        chat_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chat_{timestamp}.json"
        
        chat_file = chat_dir / filename
        with open(chat_file, 'w') as f:
            json.dump({
                'project_path': str(project_path),
                'timestamp': datetime.now().isoformat(),
                'question_count': len(history),
                'conversation': history
            }, f, indent=2)
            
        console.print(f"[green]Conversation saved to: {chat_file}[/green]")
        
    except Exception as e:
        console.print(f"[red]Failed to save conversation: {e}[/red]")


@app.command()
def models():
    """Show available models and switch default model."""
    project_path = Path.cwd()
    config_manager = ConfigManager(project_path)
    
    # Load configuration
    config = config_manager.load()
    if not config:
        console.print("[bold red]Project not initialized. Run 'sage setup' first.[/bold red]")
        raise typer.Exit(1)
        
    # Initialize model manager
    model_manager = ModelManager(config)
    
    # Show current model
    current_provider, current_model = model_manager.get_current_model_info()
    console.print(Panel(
        f"[bold]Current Default Model:[/bold]\n"
        f"🤖 {current_provider.title()} {current_model}\n"
        f"{model_manager.get_model_description(current_provider, current_model)}",
        title="Current Configuration",
        border_style="blue"
    ))
    
    # Show configured providers
    configured = model_manager.get_configured_providers()
    console.print(f"\n[bold]Configured Providers:[/bold] {', '.join([p.title() for p in configured])}")
    
    # Show recommendations
    recommendations = model_manager.get_recommended_models()
    if recommendations:
        console.print("\n[bold]Recommended Models by Use Case:[/bold]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Use Case", style="cyan")
        table.add_column("Provider", style="green") 
        table.add_column("Model", style="yellow")
        table.add_column("Status", style="white")
        table.add_column("Description", style="dim")
        
        detailed_recs = model_manager.get_detailed_recommendations()
        for use_case, details in detailed_recs.items():
            status = "✅ Ready" if details["available"] else "❌ Not configured"
            description = details["description"]
            table.add_row(
                use_case.title(), 
                details["provider"].title(), 
                details["model"], 
                status,
                description
            )
            
        console.print(table)
        
        # Show embedding information
        console.print(f"\n[bold]📊 Embedding Models by Provider:[/bold]")
        provider_comparison = model_manager.get_provider_comparison()
        
        embed_table = Table(show_header=True, header_style="bold blue")
        embed_table.add_column("Provider", style="cyan")
        embed_table.add_column("Embedding Model", style="yellow")
        embed_table.add_column("Best For", style="green")
        embed_table.add_column("Privacy", style="magenta")
        
        for provider, info in provider_comparison.items():
            embed_table.add_row(
                info["name"],
                info["embeddings"],
                info["best_for"],
                info["privacy"]
            )
            
        console.print(embed_table)
    
    # Show all available models
    console.print(f"\n[bold]All Available Models:[/bold]")
    models_list = model_manager.list_available_models()
    
    # Group by provider
    by_provider = {}
    for provider, model, available in models_list:
        if provider not in by_provider:
            by_provider[provider] = []
        by_provider[provider].append((model, available))
    
    for provider, model_list in by_provider.items():
        available_models = [m for m, a in model_list if a]
        unavailable_models = [m for m, a in model_list if not a]
        
        provider_status = "✅" if available_models else "❌" 
        console.print(f"\n{provider_status} [bold]{provider.title()}:[/bold]")
        
        if available_models:
            for model in available_models:
                console.print(f"  ✓ {model}")
        if unavailable_models:
            console.print(f"  [dim]Not configured: {', '.join(unavailable_models[:3])}{'...' if len(unavailable_models) > 3 else ''}[/dim]")
    
    # Show switching tips
    switching_tips = model_manager.get_switching_tips()
    console.print(f"\n[bold]💡 Model Switching Tips:[/bold]")
    for tip in switching_tips:
        console.print(f"  • {tip}")
        
    console.print(f"\n[dim]Use 'sage chat' and '/switch <provider> <model>' to change models during conversation[/dim]")


@app.command()
def version():
    """Show Sage version."""
    from sage import __version__
    console.print(f"Project Sage v{__version__}")


def main():
    """Main entry point for the CLI."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        raise typer.Exit(0)
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    main()