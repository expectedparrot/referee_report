"""Referee Report Generator.

A command-line tool for generating academic paper reviews using EDSL's AI models.
Processes PDF files and generates comprehensive referee reports in multiple formats.
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pip",
#   "edsl @ file:///Users/johnhorton/tools/ep/edsl",
#   "click",
#   "pyperclip",
# ]
# ///

import tempfile
from pathlib import Path
from typing import Optional

import click
import pyperclip
from edsl import FileStore, Model, QuestionFreeText, Scenario, Survey

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
    click.echo(f"Processing PDF file: {pdf_file}")
    if pages:
        click.echo(f"Limiting to first {pages} pages")

    from edsl import Cache

    # Create FileStore scenario with optional page limit
    file_store_kwargs = {'path': str(pdf_file)}
    if pages:
        file_store_kwargs['pages'] = pages
    
    paper = Scenario({'paper': FileStore(**file_store_kwargs)})
    
    # Push paper to Coop if requested
    coop_info = None
    if to_coop:
        coop_info = paper.push(description=f"Paper being reviewed: {pdf_file.name}")
        print(f"INFO: Paper pushed to Coop: {coop_info}")

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
    survey = Survey([review_question])
    
    # Execute the survey across all models
    results = survey.by(paper).by(models).run(
        verbose=True, 
        disable_remote_inference=True
    )

    # Define report template for formatting results
    report_template = """#
# Review by {{ model }}
{{full_review}}

"""
    
    if clipboard:
        # Format and copy results to clipboard
        formatted_text = results.report_from_template(
            template=report_template, 
            format='text'
        )
        pyperclip.copy(str(formatted_text))
        print("Report copied to clipboard!")
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
            print(f"Report written to temporary file: {temp_filename}")
            
            # Push review to Coop with reference to original paper
            review_filestore = FileStore(str(temp_filename))
            paper_url = coop_info['url'] if coop_info else 'unknown'
            review_info = review_filestore.push(
                description=f"Review of paper: {pdf_file.name}. Paper at {paper_url}"
            )
            print(f"INFO: Review pushed to Coop: {review_info}")
        else:
            # Save to local DOCX file
            output_filename = f"referee_report_{pdf_file.stem}.docx"
            results.report_from_template(
                template=report_template, 
                format='docx'
            ).save(output_filename)
            print(f"Report generated: {output_filename}")


if __name__ == '__main__':
    main()