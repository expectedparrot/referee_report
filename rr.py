"""Referee Report Generator.

A command-line tool for generating academic paper reviews using EDSL's AI models.
Processes PDF files and generates comprehensive referee reports in multiple formats.
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pip",
#   "edsl @ git+https://github.com/expectedparrot/edsl.git@main",
#   "click",
#   "pyperclip",
#   "rich",
# ]
# ///

import tempfile
import textwrap
from pathlib import Path
from typing import Optional

import click
import pyperclip
from edsl import FileStore, Model, QuestionFreeText, Scenario, Survey
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

console = Console()

@click.command()
@click.argument('pdf_file', type=click.Path(exists=True, path_type=Path))
@click.option(
    '--output', '-o', 
    type=click.Path(path_type=Path), 
    help='Output file for results'
)
@click.option(
    '--pages', '-p', 
    type=int, 
    help='Number of pages to process from the beginning of the PDF'
)
@click.option(
    '--prompt', 
    default='Write a full economics-style critical review of this paper:', 
    help='Prompt to use for the review (default: economics-style critical review)'
)
@click.option(
    '--clipboard', 
    is_flag=True, 
    help='Copy output to clipboard instead of saving to file'
)
@click.option(
    '--to_coop', 
    is_flag=True, 
    help='Write docx to a named temporary file and push to Coop'
)
def main(
    pdf_file: Path, 
    output: Optional[Path] = None, 
    pages: Optional[int] = None, 
    prompt: Optional[str] = None, 
    clipboard: bool = False, 
    to_coop: bool = False
) -> None:
    """Generate referee reports for academic papers using AI models.
    
    This tool processes PDF files containing academic papers and generates
    comprehensive referee reports using multiple AI models (Claude, Gemini, GPT).
    The output can be saved as DOCX files, copied to clipboard, or pushed to Coop.
    
    Args:
        pdf_file: Path to the input PDF file to process.
        output: Optional output file path for results.
        pages: Optional limit on number of pages to process from PDF start.
        prompt: Custom prompt for the review generation.
        clipboard: If True, copy output to clipboard instead of saving.
        to_coop: If True, create temporary DOCX and push to Coop platform.
        
    Examples:
        rr.py paper.pdf
        rr.py paper.pdf --pages 10 --clipboard
        rr.py paper.pdf --to_coop --prompt "Provide a technical review"
    """
    console.print(f"[bold blue]Processing PDF file:[/bold blue] {pdf_file}")
    if pages:
        console.print(f"[yellow]Limiting to first {pages} pages[/yellow]")

    from edsl.extensions.authoring.trigger_login import trigger_login

    trigger_login()

    # Create FileStore scenario with optional page limit
    file_store_kwargs = {'path': str(pdf_file)}
    if pages:
        file_store_kwargs['pages'] = pages
    
    paper = Scenario({'paper': FileStore(**file_store_kwargs)})
    
    # Push paper to Coop if requested
    coop_info = None
    if to_coop:
        with console.status("[bold green]Pushing paper to Coop..."):
            coop_info = paper.push(description=f"Paper being reviewed: {pdf_file.name}")
        
        # Create a nice table for Coop info
        table = Table(title="📄 Paper Pushed to Coop", show_header=True, header_style="bold magenta")
        table.add_column("Property", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")
        
        table.add_row("URL", coop_info['url'])
        table.add_row("Alias URL", coop_info['alias_url'])
        table.add_row("UUID", coop_info['uuid'])
        table.add_row("Version", coop_info['version'])
        table.add_row("Visibility", coop_info['visibility'])
        
        console.print(table)

    # Configure AI models for review generation
    models = [
        Model("claude-opus-4-20250514", service_name="anthropic"),
        Model("gemini-2.0-flash-exp", service_name="google"),
        Model(
            "o1-preview", 
            service_name="openai",
            reasoning_tokens=100_000,
            max_completion_tokens=100_000,
            max_tokens=32_768
        )
    ]
    
    # Create the review question with the specified prompt
    review_question = QuestionFreeText(
        question_text=f'{prompt} {{{{scenario.paper}}}}', 
        question_name='full_review'
    )
    q_response_to_review = QuestionFreeText(
        question_name = 'response_to_review', 
        question_text = textwrap.dedent("""\
        You submitted this paper: {{ scenario.paper}}. You received this review {{ full_review.answer}}. 
        Please write a detailed response to the review.
        Push back on critiques that you don't agree with or that you think are wrong and explain why. 
        Support your arguments with evidence from the paper.
    """)

    survey = Survey([review_question, q_response_to_review])
    
    # Execute the survey across all models
    with console.status("[bold green]Generating reviews with AI models..."):
        results = survey.by(paper).by(models).run()
    
    console.print("[bold green]✅ Reviews generated successfully![/bold green]")

    # Define report template for formatting results
    report_template = """#
# Review by {{ model }}
{{full_review}}

## Response to Review

{{response_to_review}}

"""
    
    if clipboard:
        # Format and copy results to clipboard
        formatted_text = results.report_from_template(
            template=report_template, 
            format='text'
        )
        pyperclip.copy(str(formatted_text))
        console.print("[bold green]📋 Report copied to clipboard![/bold green]")
    else:
        if to_coop:
            # Create temporary DOCX file and push to Coop
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
                temp_filename = temp_file.name
            
            # Generate and save DOCX report
            results.report_from_template(
                template=report_template, 
                format='docx'
            ).save(temp_filename)
            console.print(f"[dim]Report written to temporary file: {temp_filename}[/dim]")
            
            # Push review to Coop with reference to original paper
            with console.status("[bold green]Pushing review to Coop..."):
                review_filestore = FileStore(str(temp_filename))
                paper_url = coop_info['url'] if coop_info else 'unknown'
                review_info = review_filestore.push(
                    description=f"Review of paper: {pdf_file.name}. Paper at {paper_url}"
                )
            
            # Create a nice table for review Coop info
            review_table = Table(title="📝 Review Pushed to Coop", show_header=True, header_style="bold magenta")
            review_table.add_column("Property", style="cyan", no_wrap=True)
            review_table.add_column("Value", style="white")
            
            review_table.add_row("URL", review_info['url'])
            review_table.add_row("Alias URL", review_info['alias_url'])
            review_table.add_row("UUID", review_info['uuid'])
            review_table.add_row("Version", review_info['version'])
            review_table.add_row("Visibility", review_info['visibility'])
            
            console.print(review_table)
        else:
            # Save to local DOCX file
            output_filename = f"referee_report_{pdf_file.stem}.docx"
            results.report_from_template(
                template=report_template, 
                format='docx'
            ).save(output_filename)
            console.print(f"[bold green]📄 Report generated:[/bold green] [cyan]{output_filename}[/cyan]")


if __name__ == '__main__':
    main()