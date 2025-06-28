# Referee Report Generator

A command-line tool for generating comprehensive academic paper reviews using multiple AI models through the EDSL framework.

## Overview

This tool processes PDF files containing academic papers and generates detailed referee reports using state-of-the-art AI models including Claude, Gemini, and GPT. The generated reviews can be saved as DOCX files, copied to clipboard, or integrated with the Coop platform for collaborative research workflows.

## Features

- **Multi-Model Reviews**: Generates reviews using Claude Opus, Gemini Flash, and GPT-4 for comprehensive analysis
- **Flexible Output**: Save to DOCX, copy to clipboard, or push to Coop platform
- **Page Limiting**: Process only specific portions of large documents
- **Custom Prompts**: Customize the review style and focus
- **Economics Focus**: Default prompt optimized for economics paper reviews

## Installation

This script uses Python's inline script dependencies feature. Ensure you have Python 3.11+ installed.

The script will automatically manage its dependencies:
- `edsl` - AI survey framework
- `click` - Command-line interface
- `pyperclip` - Clipboard operations

## Usage

### Basic Usage

```bash
python rr.py paper.pdf
```

This will generate a referee report and save it as `referee_report_paper.docx` in the current directory.

### Command Line Options

```bash
python rr.py [OPTIONS] PDF_FILE
```

**Arguments:**
- `PDF_FILE`: Path to the input PDF file to review (required)

**Options:**
- `-o, --output PATH`: Specify output file path
- `-p, --pages INTEGER`: Limit processing to first N pages of the PDF
- `--prompt TEXT`: Custom prompt for review generation (default: economics-style critical review)
- `--clipboard`: Copy output to clipboard instead of saving to file
- `--to_coop`: Create temporary DOCX file and push to Coop platform
- `--help`: Show help message

### Examples

**Generate a standard review:**
```bash
python rr.py research_paper.pdf
```

**Review only the first 10 pages:**
```bash
python rr.py long_paper.pdf --pages 10
```

**Copy review to clipboard:**
```bash
python rr.py paper.pdf --clipboard
```

**Use custom prompt:**
```bash
python rr.py paper.pdf --prompt "Provide a technical review focusing on methodology"
```

**Push to Coop platform:**
```bash
python rr.py paper.pdf --to_coop
```

## AI Models Used

The tool employs three different AI models to provide diverse perspectives:

1. **Claude Opus 4** (Anthropic) - Advanced reasoning and analysis
2. **Gemini 2.0 Flash** (Google) - Fast, comprehensive reviews  
3. **GPT-4 Preview** (OpenAI) - In-depth critical analysis with extended reasoning

## Output Format

Reviews are formatted with clear model attribution:

```
# Review by claude-opus-4-20250514
[Detailed review content...]

# Review by gemini-2.0-flash-exp  
[Detailed review content...]

# Review by o1-preview
[Detailed review content...]
```

## Configuration

The tool runs with these default settings:
- **Verbose output**: Progress tracking during generation
- **Local inference**: Disabled remote inference for faster processing
- **Extended reasoning**: GPT-4 configured with 100K reasoning tokens
- **High token limits**: Up to 100K completion tokens for comprehensive reviews

## Coop Integration

When using the `--to_coop` flag:
1. The original paper is pushed to Coop with descriptive metadata
2. The generated review is saved as a temporary DOCX file
3. The review file is pushed to Coop with a reference to the original paper
4. Both items are available for collaborative review and sharing

## Error Handling

The tool includes robust error handling for:
- Invalid PDF files
- Network connectivity issues
- AI model availability
- File system permissions
- Clipboard operations

## Requirements

- Python 3.11 or higher
- Internet connection for AI model access
- Valid API keys for Anthropic, Google, and OpenAI services (configured in EDSL)

## Troubleshooting

**"File not found" error**: Ensure the PDF file path is correct and the file exists.

**API errors**: Verify your AI service API keys are properly configured in your EDSL environment.

**Memory issues with large PDFs**: Use the `--pages` option to limit processing to essential sections.

**Clipboard not working**: Ensure you have proper clipboard access permissions on your system.

## Contributing

This tool is part of the EDSL extensions ecosystem. For issues or feature requests, please refer to the main EDSL documentation and support channels.