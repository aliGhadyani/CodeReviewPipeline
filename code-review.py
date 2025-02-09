import os
import json
import subprocess
import ollama
import git
import sys
from pathlib import Path

# Load repository path from input argument
if len(sys.argv) < 2:
    print("Usage: python code_review.py <repository_path>")
    sys.exit(1)

REPO_PATH = sys.argv[1]

# Load rules from JSON file
def load_rules():
    with open("rules.json", "r") as file:
        return json.load(file)

RULES = load_rules()

# Mapping file extensions to languages
EXT_TO_LANG = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".java": "Java",
    ".c": "C",
    ".cpp": "C++",
    ".cs": "C#",
    ".go": "Go",
    ".rb": "Ruby",
    ".php": "PHP",
    ".rs": "Rust",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".html": "HTML",
    ".css": "CSS",
    ".sh": "Shell",
    ".sql": "SQL"
}

# Detect programming language based on file extension
def detect_language(file_path):
    ext = os.path.splitext(file_path)[1]
    return EXT_TO_LANG.get(ext, "Unknown")

# Fetch latest code changes
def get_latest_code():
    repo = git.Repo(REPO_PATH)
    repo.git.pull()
    print("Pulled latest code.")

# Run static analysis tools
def run_static_analysis():
    print("Running static analysis...")

    # Python
    subprocess.run(["flake8", REPO_PATH], check=False)
    subprocess.run(["bandit", "-r", REPO_PATH], check=False)

    # JavaScript / TypeScript
    subprocess.run(["eslint", REPO_PATH], check=False)

    # C / C++ / Java (Using Clang-Tidy)
    subprocess.run(["clang-tidy", "-p", REPO_PATH], check=False)

# AI-powered code review using Ollama
def ai_code_review(file_path):
    language = detect_language(file_path)
    if language == "Unknown":
        return f"Skipping {file_path}, unknown language."

    rules = RULES.get(language, {}).get("rules", ["No specific rules available."])
    formatted_rules = "\n".join([f"- {rule}" for rule in rules])

    with open(file_path, "r") as f:
        code_content = f.read()

    prompt = f"""
    Review the following {language} code based on these rules:

    {formatted_rules}

    Code:
    {code_content}
    """

    response = ollama.chat(model="deepseek-r1:1.5b", messages=[{"role": "user", "content": prompt}])
    return response['message']['content']

# Generate AI Review Report
def generate_report(reviews):
    report_path = os.path.join(REPO_PATH, "code_review_report.md")
    with open(report_path, "w") as report:
        report.write("# Code Review Report\n\n")
        for file, feedback in reviews.items():
            report.write(f"## {file}\n\n```\n{feedback}\n```\n\n")
    print(f"Report generated: {report_path}")
    return report_path

# Send report to Slack (optional)
def send_slack_notification(report_path):
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
    if not SLACK_WEBHOOK_URL:
        print("No Slack Webhook URL found, skipping Slack notification.")
        return

    message = f"Code Review Completed! Report available at: {report_path}"
    subprocess.run(["curl", "-X", "POST", "-H", "Content-type: application/json", 
                    "--data", f'{{"text": "{message}"}}', SLACK_WEBHOOK_URL])

# Read .gitignore and return ignored patterns
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

# Check if a file is ignored based on .gitignore patterns
def is_ignored(file_path, ignored_patterns):
    relative_path = os.path.relpath(file_path, REPO_PATH)
    for pattern in ignored_patterns:
        if pattern.endswith("/"):
            if relative_path.startswith(pattern):
                return True
        elif relative_path == pattern or relative_path.startswith(pattern):
            return True
    return False

# Get all files in the repository (excluding .gitignore files)
def get_all_files():
    ignored_patterns = get_gitignore_patterns()
    all_files = []
    
    for root, _, files in os.walk(REPO_PATH):
        for file in files:
            if file.startswith("."):  # Skip hidden files
                continue
            file_path = os.path.join(root, file)
            if detect_language(file_path) != "Unknown" and not is_ignored(file_path, ignored_patterns):
                all_files.append(file_path)
    
    return all_files

# Main Execution
if __name__ == "__main__":
    get_latest_code()
    # run_static_analysis()

    files_to_review = get_all_files()

    reviews = {}
    for file in files_to_review:
        print(f"Reviewing {file}...")
        feedback = ai_code_review(file)
        reviews[file] = feedback
        print(f"AI Feedback:\n{feedback}")

    report_path = generate_report(reviews)
    send_slack_notification(report_path)
