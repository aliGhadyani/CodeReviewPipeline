import os
import json
import subprocess
import sys
import re
import git
from pathlib import Path
import ollama

# -------------------------------
# Helper Functions
# -------------------------------

# Clean the AI output by removing <think> tags.
def clean_ai_output(text):
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

# Load repository path from input argument.
if len(sys.argv) < 2:
    print("Usage: python code_review.py <repository_path>")
    sys.exit(1)
REPO_PATH = sys.argv[1]

# Load rules from rules.json.
def load_rules():
    with open("rules.json", "r") as file:
        return json.load(file)
RULES = load_rules()

# Mapping file extensions to languages.
EXT_TO_LANG = {
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".h": "C++",
    ".hpp": "C++"
    # Add other extensions for other languages if needed.
}

def detect_language(file_path):
    ext = os.path.splitext(file_path)[1]
    return EXT_TO_LANG.get(ext, "Unknown")

# Get .gitignore patterns.
def get_gitignore_patterns():
    gitignore_path = os.path.join(REPO_PATH, ".gitignore")
    if not os.path.exists(gitignore_path):
        return []
    patterns = []
    with open(gitignore_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
    return patterns

# Check if a file should be ignored based on .gitignore patterns.
def is_ignored(file_path, ignored_patterns):
    relative_path = os.path.relpath(file_path, REPO_PATH)
    for pattern in ignored_patterns:
        # Simple check: if the relative path starts with the pattern (for directories)
        if pattern.endswith("/") and relative_path.startswith(pattern):
            return True
        # For file patterns, check for equality or prefix match.
        elif relative_path == pattern or relative_path.startswith(pattern):
            return True
    return False

# Recursively get all files (ignoring those in .gitignore).
def get_all_files():
    ignored_patterns = get_gitignore_patterns()
    all_files = []
    for root, _, files in os.walk(REPO_PATH):
        for file in files:
            # Skip hidden files.
            if file.startswith("."):
                continue
            file_path = os.path.join(root, file)
            if detect_language(file_path) != "Unknown" and not is_ignored(file_path, ignored_patterns):
                all_files.append(file_path)
    return all_files

# -------------------------------
# AI Review Functions
# -------------------------------

# Perform AI code review for each category for a given file.
def ai_code_review_by_category(file_path):
    language = detect_language(file_path)
    if language == "Unknown":
        return {"General": "Skipping file (unknown language)."}
    
    # Retrieve the category rules for the language.
    # In our sample, we only have rules for C++.
    language_rules = RULES.get(language, {})
    if not language_rules:
        return {"General": "No rules defined for this language."}
    
    with open(file_path, "r") as f:
        code_content = f.read()
    
    category_feedback = {}
    # For each review category (e.g., Memory Safety, Syntax, Security, Performance)
    for category, rules_list in language_rules.items():
        formatted_rules = "\n".join([f"- {rule}" for rule in rules_list])
        prompt = f"""
Review the following {language} code for **{category}** issues based on following rules and nothing more:
{formatted_rules}

Code:
{code_content}
"""
        try:
            response = ollama.chat(
                model="deepseek-r1:8b",
                messages=[{"role": "user", "content": prompt}]
            )
            feedback = clean_ai_output(response['message']['content'])
        except Exception as e:
            feedback = f"Error during review: {str(e)}"
        category_feedback[category] = feedback
    return category_feedback

# -------------------------------
# Report Generation
# -------------------------------

# Generate a Markdown report with separate sections for each file and category.
def generate_report(reviews):
    report_path = os.path.join(REPO_PATH, "code_review_report.md")
    with open(report_path, "w") as report:
        report.write("# Code Review Report\n\n")
        for file, categories in reviews.items():
            report.write(f"## File: {os.path.relpath(file, REPO_PATH)}\n\n")
            for category, feedback in categories.items():
                report.write(f"### {category} Review\n\n")
                report.write(feedback)
                report.write("\n\n")
    print(f"Report generated: {report_path}")
    return report_path

# -------------------------------
# Other Functions (Static Analysis, Slack)
# -------------------------------

def get_latest_code():
    repo = git.Repo(REPO_PATH)
    repo.git.pull()
    print("Pulled latest code.")

def run_static_analysis():
    print("Running static analysis...")
    # Example: run clang-tidy for C++ code (customize as needed)
    subprocess.run(["clang-tidy", "-p", REPO_PATH], check=False)

def send_slack_notification(report_path):
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
    if not SLACK_WEBHOOK_URL:
        print("No Slack Webhook URL found, skipping Slack notification.")
        return
    message = f"Code Review Completed! Report available at: {report_path}"
    subprocess.run(["curl", "-X", "POST", "-H", "Content-type: application/json",
                    "--data", f'{{"text": "{message}"}}', SLACK_WEBHOOK_URL])

# -------------------------------
# Main Execution
# -------------------------------

if __name__ == "__main__":
    get_latest_code()
    # run_static_analysis()

    files_to_review = get_all_files()
    reviews = {}
    for file in files_to_review:
        print(f"Reviewing {file}...")
        category_feedback = ai_code_review_by_category(file)
        reviews[file] = category_feedback
        for category, feedback in category_feedback.items():
            print(f"--- {category} Review ---\n{feedback}\n")
    
    report_path = generate_report(reviews)
    # send_slack_notification(report_path)
