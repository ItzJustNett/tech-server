import tempfile
import os
import re
import markdown
import subprocess
import shutil
from pathlib import Path

def clean_markdown_content(markdown_text):
    """
    Remove any potentially sensitive information from markdown content
    
    Args:
        markdown_text (str): Raw markdown content
        
    Returns:
        str: Cleaned markdown content
    """
    # Remove any YAML frontmatter
    markdown_text = re.sub(r'^---[\s\S]*?---\n', '', markdown_text)
    
    # Remove any user styling tags
    markdown_text = re.sub(r'<userStyle>.*?</userStyle>', '', markdown_text)
    
    return markdown_text

def convert_text_to_html(markdown_text, output_html=None):
    """
    Convert Markdown text to HTML with minimal styling
    
    Args:
        markdown_text (str): Markdown text content
        output_html (str, optional): Path for the output HTML file
    
    Returns:
        str: Path to the generated HTML file
    """
    # Set default output to a temporary file if not provided
    if output_html is None:
        temp_dir = tempfile.mkdtemp()
        output_html = os.path.join(temp_dir, "temp.html")
    
    # Clean the content
    markdown_text = clean_markdown_content(markdown_text)
    
    # Convert to HTML
    html_content = markdown.markdown(
        markdown_text, 
        extensions=['extra', 'codehilite', 'tables']
    )
    
    # Add minimal styling without any system info
    styled_html = f"""<!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                margin: 1.5cm; 
                line-height: 1.5;
                color: #333;
            }}
            h1, h2, h3, h4, h5, h6 {{ 
                color: #333; 
                margin-top: 1.5em;
                margin-bottom: 0.5em;
            }}
            code, pre {{
                font-family: "Courier New", Courier, monospace;
                background-color: #f5f5f5;
                padding: 2px 4px;
                border-radius: 3px;
            }}
            pre {{
                padding: 10px;
                overflow-x: auto;
                white-space: pre-wrap;
                margin: 1em 0;
            }}
            a {{
                color: #0066cc;
                text-decoration: none;
            }}
            img {{
                max-width: 100%;
                height: auto;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            blockquote {{
                border-left: 4px solid #ddd;
                padding-left: 1em;
                margin-left: 0;
                color: #555;
            }}
            hr {{
                border: none;
                height: 1px;
                background-color: #ddd;
                margin: 2em 0;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Write the HTML file
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(styled_html)
    
    return output_html

def print_with_browser(html_file, output_pdf=None, browser='edge'):
    """
    Print HTML file to PDF using a browser in headless mode
    
    Args:
        html_file (str): Path to the HTML file
        output_pdf (str, optional): Path for the output PDF file
        browser (str): Browser to use ('edge' or 'chrome')
    
    Returns:
        str: Path to the generated PDF file
    """
    if output_pdf is None:
        output_pdf = os.path.splitext(html_file)[0] + '.pdf'
    
    # Get absolute paths
    html_path = os.path.abspath(html_file)
    pdf_path = os.path.abspath(output_pdf)
    
    # File URL format
    file_url = f"file:///{html_path.replace(os.sep, '/')}"
    
    # Determine browser executable
    if browser == 'edge':
        executable = "msedge"
    else:  # chrome
        # Try different Chrome executable paths
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            "chrome",
            "google-chrome"
        ]
        
        executable = None
        for path in chrome_paths:
            try:
                if os.path.exists(path):
                    executable = path
                    break
                else:
                    # Try running which command
                    result = subprocess.run(["where", path] if os.name == 'nt' else ["which", path], 
                                        capture_output=True, text=True)
                    if result.returncode == 0:
                        executable = result.stdout.strip()
                        break
            except:
                continue
                
        if not executable:
            return None
    
    # Command to launch browser in headless mode and print to PDF
    cmd = [
        executable,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",  # Sometimes needed in certain environments
        "--disable-extensions",
        f"--print-to-pdf={pdf_path}",
        file_url
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=30)
        if os.path.exists(pdf_path):
            return pdf_path
        return None
    except subprocess.CalledProcessError:
        return None
    except subprocess.TimeoutExpired:
        return None

def text_to_pdf(text, filename=None):
    """
    Convert text to PDF
    
    Args:
        text (str): Text to convert to PDF
        filename (str, optional): Desired filename for the PDF
    
    Returns:
        str: Path to the generated PDF file
    """
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    
    # Set default output filename if not provided
    if filename is None:
        output_pdf = os.path.join(temp_dir, "output.pdf")
    else:
        # Ensure filename ends with .pdf
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'
        output_pdf = os.path.join(temp_dir, filename)
    
    # First convert to HTML
    temp_html = os.path.join(temp_dir, "temp.html")
    html_file = convert_text_to_html(text, temp_html)
    
    # Try conversion methods in order
    methods = [
        lambda: print_with_browser(html_file, output_pdf, 'edge'),
        lambda: print_with_browser(html_file, output_pdf, 'chrome'),
    ]
    
    for method in methods:
        try:
            result = method()
            if result and os.path.exists(result):
                return result
        except Exception:
            continue
    
    # If all conversion methods fail, return None
    return None

# For testing the module directly
if __name__ == "__main__":
    test_text = """# Test Document
    
    This is a test of the PDF converter.
    
    ## Features
    
    - Converts markdown to PDF
    - Supports formatting like **bold** and *italic*
    - Creates nice looking documents
    
    > This is a blockquote for testing
    """
    
    result = text_to_pdf(test_text, "test_output.pdf")
    if result:
        print(f"PDF created at: {result}")
    else:
        print("Failed to create PDF")