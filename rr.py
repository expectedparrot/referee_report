# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pip",
#   "edsl @ file:///Users/johnhorton/tools/ep/edsl",
#   "click",
#   "pyperclip",
# ]
# ///

import click
import pyperclip
import tempfile
from edsl import QuestionFreeText, FileStore, Scenario, Model, Survey
from pathlib import Path

@click.command()
@click.argument('pdf_file', type=click.Path(exists=True, path_type=Path))
@click.option('--output', '-o', type=click.Path(path_type=Path), help='Output file for results')
@click.option('--pages', '-p', type=int, help='Number of pages to process from the beginning of the PDF')
@click.option('--prompt', default='Write a full economics-style critical review of this paper:', help='Prompt to use for the review (default: economics-style critical review)')
@click.option('--clipboard', is_flag=True, help='Copy output to clipboard instead of saving to file')
@click.option('--to_coop', is_flag=True, help='Write docx to a named temporary file')
def main(pdf_file: Path, output: Path = None, pages: int = None, prompt: str = None, clipboard: bool = False, to_coop: bool = False):
    """
    Process a PDF file using EDSL QuestionFreeText.
    
    PDF_FILE: Path to the input PDF file to process
    """
    click.echo(f"Processing PDF file: {pdf_file}")
    if pages:
        click.echo(f"Limiting to first {pages} pages")

    from edsl import Cache

    # Create FileStore with optional page limit
    if pages:
        paper = Scenario({'paper': FileStore(str(pdf_file), pages=pages)})
    else:
        paper = Scenario({'paper': FileStore(str(pdf_file))})
    
    if to_coop:
        info = paper.push(description = "Paper being reviewed: " + pdf_file.name)
        print(f"INFO: Paper pushed to Coop: {info}")

    models = [Model("claude-opus-4-20250514", service_name = "anthropic"), 
              Model("gemini-2.0-flash-exp", service_name = "google"), 
              Model("o1-preview", service_name = "openai", 
                    reasoning_tokens = 100_000, 
                    max_completion_tokens = 100_000,
                    max_tokens = 32_768
                    )]
    # Create the question with the specified prompt

    q_full_review = QuestionFreeText(question_text = f'{prompt} {{{{scenario.paper}}}}', question_name = 'full_review')
    survey = Survey([q_full_review])
    results = survey.by(paper).by(models).run(verbose = True, disable_remote_inference = True)

    
    template = """#
# Review by {{ model }}
{{full_review}}

"""
    
    if clipboard:
        # Get the formatted text and copy to clipboard
        formatted_text = results.report_from_template(template=template, format='text')
        pyperclip.copy(str(formatted_text))
        print("Report copied to clipboard!")
    else:
        # Save to file
        if to_coop:
            # Create a named temporary file
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
                temp_filename = temp_file.name
            results.report_from_template(template = template, format = 'docx').save(temp_filename)
            print(f"Report written to temporary file: {temp_filename}")
            review = FileStore(str(temp_filename))
            review_info = review.push(
                description = f"Review of paper:{pdf_file.name}. Paper at {info['url']}")
            print(f"INFO: Review pushed to Coop: {review_info}")
        else:
            output_filename = f"referee_report_{pdf_file.stem}.docx"
            results.report_from_template(template = template, format = 'docx').save(output_filename)
            print(f"Report generated: {output_filename}")


if __name__ == '__main__':
    main()