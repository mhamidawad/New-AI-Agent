"""Command-line interface for the AI Coding Agent."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from .core.agent import CodingAgent
from .core.config import Config


console = Console()


@click.group()
@click.option('--config', type=click.Path(), help='Configuration file path')
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--verbose', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, config: Optional[str], debug: bool, verbose: bool):
    """AI Coding Agent - Intelligent coding assistant powered by AI."""
    ctx.ensure_object(dict)
    
    # Load configuration
    if config:
        ctx.obj['config'] = Config.load(config)
    else:
        ctx.obj['config'] = Config.from_env()
    
    # Override with CLI flags
    if debug:
        ctx.obj['config'].agent.debug = True
    if verbose:
        ctx.obj['config'].agent.verbose = True


@cli.command()
@click.pass_context
def chat(ctx):
    """Start an interactive chat session with the agent."""
    config = ctx.obj['config']
    
    console.print(Panel("[bold green]AI Coding Agent[/bold green]", subtitle="Interactive Chat Mode"))
    console.print("Type 'exit' to quit, 'help' for commands, or 'clear' to clear context.\n")
    
    async def chat_session():
        agent = CodingAgent(config)
        
        while True:
            try:
                # Get user input
                user_input = Prompt.ask("[bold blue]You[/bold blue]")
                
                if user_input.lower() in ['exit', 'quit']:
                    console.print("[yellow]Goodbye![/yellow]")
                    break
                elif user_input.lower() == 'help':
                    show_chat_help()
                    continue
                elif user_input.lower() == 'clear':
                    agent.context_manager.clear_context()
                    console.print("[green]Context cleared.[/green]")
                    continue
                elif user_input.lower() == 'status':
                    show_status(agent)
                    continue
                
                # Get response from agent
                with console.status("[bold green]Thinking...[/bold green]"):
                    response = await agent.chat(user_input)
                
                # Display response
                console.print(Panel(response, title="[bold green]Assistant[/bold green]"))
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
    
    asyncio.run(chat_session())


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--format', type=click.Choice(['json', 'table']), default='table', help='Output format')
@click.pass_context
def analyze(ctx, file_path: str, format: str):
    """Analyze a code file."""
    config = ctx.obj['config']
    
    async def analyze_file():
        agent = CodingAgent(config)
        
        with console.status(f"[bold green]Analyzing {file_path}...[/bold green]"):
            result = await agent.analyze_file(file_path)
        
        if format == 'json':
            import json
            console.print_json(json.dumps(result, indent=2))
        else:
            display_analysis_table(result)
    
    asyncio.run(analyze_file())


@cli.command()
@click.argument('description')
@click.option('--language', default='python', help='Programming language')
@click.option('--output', type=click.Path(), help='Output file path')
@click.pass_context
def generate(ctx, description: str, language: str, output: Optional[str]):
    """Generate code from description."""
    config = ctx.obj['config']
    
    async def generate_code():
        agent = CodingAgent(config)
        
        with console.status(f"[bold green]Generating {language} code...[/bold green]"):
            code = await agent.generate_code(description, language)
        
        # Display code
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title=f"[bold green]Generated {language.title()} Code[/bold green]"))
        
        # Save to file if requested
        if output:
            with open(output, 'w') as f:
                f.write(code)
            console.print(f"[green]Code saved to {output}[/green]")
    
    asyncio.run(generate_code())


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.pass_context
def review(ctx, file_path: str):
    """Review code and provide feedback."""
    config = ctx.obj['config']
    
    async def review_code():
        agent = CodingAgent(config)
        
        # Read file
        with open(file_path, 'r') as f:
            code = f.read()
        
        # Detect language
        language = agent._detect_language(file_path)
        
        with console.status(f"[bold green]Reviewing {file_path}...[/bold green]"):
            review = await agent.review_code(code, language)
        
        console.print(Panel(review, title=f"[bold blue]Code Review: {file_path}[/bold blue]"))
    
    asyncio.run(review_code())


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.argument('error_message')
@click.pass_context
def fix(ctx, file_path: str, error_message: str):
    """Fix code errors."""
    config = ctx.obj['config']
    
    async def fix_code():
        agent = CodingAgent(config)
        
        # Read file
        with open(file_path, 'r') as f:
            code = f.read()
        
        # Detect language
        language = agent._detect_language(file_path)
        
        with console.status(f"[bold green]Fixing {file_path}...[/bold green]"):
            fixed_code = await agent.fix_code(code, error_message, language)
        
        console.print(Panel(fixed_code, title=f"[bold green]Fixed Code[/bold green]"))
        
        # Ask if user wants to save
        if Prompt.ask("Save fixed code to file?", choices=['y', 'n'], default='n') == 'y':
            with open(file_path, 'w') as f:
                f.write(fixed_code)
            console.print(f"[green]Fixed code saved to {file_path}[/green]")
    
    asyncio.run(fix_code())


@cli.command()
@click.argument('project_path', type=click.Path(exists=True), default='.')
@click.pass_context
def overview(ctx, project_path: str):
    """Get project overview and analysis."""
    config = ctx.obj['config']
    
    async def analyze_project():
        agent = CodingAgent(config)
        
        with console.status(f"[bold green]Analyzing project {project_path}...[/bold green]"):
            result = await agent.analyze_project(project_path)
        
        display_project_overview(result)
    
    asyncio.run(analyze_project())


@cli.command()
@click.pass_context
def status(ctx):
    """Show agent status and configuration."""
    config = ctx.obj['config']
    agent = CodingAgent(config)
    show_status(agent)


def show_chat_help():
    """Show chat commands help."""
    help_table = Table(title="Chat Commands")
    help_table.add_column("Command", style="cyan")
    help_table.add_column("Description", style="white")
    
    commands = [
        ("exit, quit", "Exit the chat session"),
        ("help", "Show this help message"),
        ("clear", "Clear conversation context"),
        ("status", "Show agent status"),
    ]
    
    for command, description in commands:
        help_table.add_row(command, description)
    
    console.print(help_table)


def show_status(agent: CodingAgent):
    """Show agent status."""
    status_info = agent.get_status()
    
    status_table = Table(title="Agent Status")
    status_table.add_column("Property", style="cyan")
    status_table.add_column("Value", style="white")
    
    status_table.add_row("Model", status_info["model"])
    status_table.add_row("Provider", status_info["provider"])
    status_table.add_row("Debug Mode", str(status_info["config"]["debug"]))
    status_table.add_row("Tools Enabled", str(status_info["config"]["tools_enabled"]))
    
    context = status_info["context"]
    status_table.add_row("Session ID", context["session_id"])
    status_table.add_row("Messages", str(context["message_count"]))
    status_table.add_row("Files in Context", str(context["file_count"]))
    
    console.print(status_table)


def display_analysis_table(result):
    """Display analysis results in table format."""
    console.print(f"[bold green]Analysis Results for {result['file_path']}[/bold green]\n")
    
    # Basic stats
    if 'analysis' in result and 'basic_stats' in result['analysis']:
        stats = result['analysis']['basic_stats']
        stats_table = Table(title="Basic Statistics")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="white")
        
        for key, value in stats.items():
            stats_table.add_row(key.replace('_', ' ').title(), str(value))
        
        console.print(stats_table)
    
    # Complexity
    if 'analysis' in result and 'complexity' in result['analysis']:
        complexity = result['analysis']['complexity']
        if not isinstance(complexity, dict) or 'error' not in complexity:
            console.print(f"\n[bold blue]Complexity Metrics:[/bold blue]")
            for key, value in complexity.items():
                console.print(f"  {key.replace('_', ' ').title()}: {value}")


def display_project_overview(result):
    """Display project overview."""
    analysis = result['analysis']
    
    overview_table = Table(title=f"Project Overview: {result['project_path']}")
    overview_table.add_column("Property", style="cyan")
    overview_table.add_column("Value", style="white")
    
    overview_table.add_row("Total Files", str(analysis['file_count']))
    overview_table.add_row("Total Size", f"{analysis['total_size']:,} bytes")
    overview_table.add_row("Languages", ", ".join(analysis['languages']))
    overview_table.add_row("Dependencies", ", ".join(analysis['dependencies']) or "None found")
    
    if analysis.get('git_info'):
        git_info = analysis['git_info']
        overview_table.add_row("Git Branch", git_info.get('branch', 'Unknown'))
        overview_table.add_row("Latest Commit", git_info.get('commit', 'Unknown'))
        overview_table.add_row("Working Dir Status", "Dirty" if git_info.get('is_dirty') else "Clean")
    
    console.print(overview_table)


def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user.[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        if '--debug' in sys.argv:
            console.print_exception()
        sys.exit(1)


if __name__ == '__main__':
    main()