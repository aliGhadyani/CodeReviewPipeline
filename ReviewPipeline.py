def ai_code_review(file_path):
    language = detect_language(file_path)
    with open(file_path, "r") as f:
        code_content = f.read()

    prompt = f"""
    Review the following {language} code based on these rules:

    {get_language_rules(language)}

    Code:
    {code_content}
    """

    response = ollama.chat(model="<your-model>", messages=[{"role": "user", "content": prompt}])
    return response['message']['content']

def get_language_rules(language):
    rules_dict = {
        "Python": "Follow PEP8, avoid print() in production, ensure proper exception handling, check for security vulnerabilities.",
        "JavaScript": "Avoid var, enforce ESLint rules, handle async errors, prevent callback hell.",
        "Java": "Follow CamelCase conventions, use final where applicable, ensure proper resource management, avoid memory leaks.",
        "C": "Check for uninitialized variables, buffer overflows, memory leaks, and missing break statements.",
        "C++": "Ensure const correctness, detect redundant object creation, enforce RAII principles.",
        "C#": "Ensure proper use of using statements, detect async void misuse, enforce naming conventions.",
        "Go": "Ensure idiomatic error handling, proper use of defer, avoid excessive goroutines.",
        "Ruby": "Avoid monkey patching, enforce indentation, detect eval() usage.",
        "PHP": "Ensure strict_types, detect SQL injection, check for CSRF protection.",
        "Rust": "Follow ownership and borrowing rules, avoid unsafe blocks, optimize memory usage.",
        "Swift": "Use guard statements, enforce explicit access control, avoid force-unwrapping.",
        "SQL": "Optimize queries, ensure proper indexing, avoid SQL injection.",
        "txt": "No specific rules available."
    }
    return rules_dict.get(language, "No specific rules available.")
