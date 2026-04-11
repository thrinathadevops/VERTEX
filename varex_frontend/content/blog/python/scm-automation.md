---
title: "Python Automation: SCMs (GitHub, GitLab, Bitbucket)"
category: "python"
date: "2026-04-11T15:45:00.000Z"
author: "Admin"
---

Source Code Management (SCM) systems like GitHub, GitLab, and Bitbucket orchestrate the entire development lifecycle. Because these platforms wrap extensive REST and GraphQL APIs around native Git operations, Python allows DevSecOps teams to perform fleet-wide security audits, automate code reviews, enforce conventional commit messaging, and synchronize infrastructure configurations automatically.

In this tutorial, we focus on 10 explicit Python automation tasks mapped directly to SCM operations across all major providers. As with prior topics, every task strictly features rationale mapping, a sample API configuration, line-by-line scripted methodology, and standardized console output.

---

### Task 1: Audit stale pull requests / merge requests

**Why use this logic?** Pull Requests (PRs) left open for 30 days cause massive merge conflicts later. Automating a Python script that polls GitHub, GitLab, or Bitbucket APIs to identify stale PRs natively prevents codebase rot and pings developers on Slack automatically.

**Example Log (SCM API Array):**
`[{"id": 101, "age_days": 45, "author": "devA"}]`

**Python Script:**
```python
def audit_stale_pull_requests(pr_api_response, threshold_days=30):
    stale_prs = []
    
    # 1. Iterate over the Pull Request dictionaries returned by the SCM API
    for pr in pr_api_response:
        age = pr.get("age_days", 0)
        
        # 2. Enforce logic limits securely
        if age > threshold_days:
             author = pr.get("author")
             pr_id = pr.get("id")
             stale_prs.append(f"PR #{pr_id} by @{author} is {age} days old.")
             
    # 3. Assess output and format reporting
    if stale_prs:
         return f"SCM AUTOMATION: Found {len(stale_prs)} stale Pull Requests!\n- " + "\n- ".join(stale_prs)
         
    return "SCM AUTOMATION: Codebase clean. No stale Pull Requests found."

# Mocked output from a generic GitHub/GitLab API call
mock_prs = [
    {"id": 880, "age_days": 4, "author": "john_doe"},
    {"id": 812, "age_days": 35, "author": "jane_smith"} # Stale
]

print(audit_stale_pull_requests(mock_prs))
```

**Output of the script:**
```text
SCM AUTOMATION: Found 1 stale Pull Requests!
- PR #812 by @jane_smith is 35 days old.
```

---

### Task 2: Automate repository creation and branch protection rules

**Why use this logic?** If a developer manually clicks "New Repo" in GitLab, they frequently forget to lock the `main` branch. Python automating repository creation via POST requests ensures that every new repository inherits enterprise branch-protection (e.g., "Requires 2 Approvers") natively by default.

**Example Log (API Payload Configuration):**
`{"name": "auth-svc", "protection": {"required_reviews": 2}}`

**Python Script:**
```python
import json

def bootstrap_secure_repository(scm_provider, repo_name):
    # 1. Define Standard Enterprise Security Defaults natively
    payload = {
        "repository_name": repo_name,
        "private": True,
        "branch_protections": {
             "branch": "main",
             "required_approving_review_count": 2,
             "enforce_admins": True,
             "block_force_pushes": True
        }
    }
    
    # 2. Transform the logic strictly based on the target provider
    if scm_provider.lower() == "github":
         api_route = f"https://api.github.com/orgs/my-org/repos"
    elif scm_provider.lower() == "gitlab":
         api_route = f"https://gitlab.com/api/v4/projects"
    elif scm_provider.lower() == "bitbucket":
         api_route = f"https://api.bitbucket.org/2.0/repositories/my-workspace/{repo_name}"
    else:
         return f"Unsupported SCM Provider: {scm_provider}"
         
    # 3. Represent logical POST operations
    # requests.post(api_route, json=payload ...)
    
    return f"[{scm_provider.upper()}] Provisioning Secure Repo: {repo_name}\nConfig:\n{json.dumps(payload, indent=2)}"

print(bootstrap_secure_repository("github", "payment-service"))
```

**Output of the script:**
```json
[GITHUB] Provisioning Secure Repo: payment-service
Config:
{
  "repository_name": "payment-service",
  "private": true,
  "branch_protections": {
    "branch": "main",
    "required_approving_review_count": 2,
    "enforce_admins": true,
    "block_force_pushes": true
  }
}
```

---

### Task 3: Search codebases for exposed secrets/keys using API scraping

**Why use this logic?** Developers accidentally commit AWS access keys. While dedicated tools like `trufflehog` exist, simple Python scripts can dynamically hit the GitHub Search API (`/search/code?q=AKIA`) on a cron job to find glaringly obvious token leaks natively without external dependencies. 

**Example Log (SCM Code Search Response payload):**
`{"total_count": 1, "items": [{"path": "config.json"}]}`

**Python Script:**
```python
def scan_for_leaked_secrets(api_search_results, secret_type):
    # 1. Parse structural response from querying (e.g. `q=AKIA` targeting AWS Keys)
    leaks_found = api_search_results.get("total_count", 0)
    
    if leaks_found == 0:
        return f"SEC-OPS AUDIT: Zero '{secret_type}' vulnerabilities found in codebase."
        
    # 2. Extract context naturally
    files_affected = []
    for item in api_search_results.get("items", []):
         file_path = item.get("path")
         repo_name = item.get("repository", {}).get("name")
         files_affected.append(f"{repo_name} -> {file_path}")
         
    # 3. Construct Security Alert
    report = f"🚨 SEC-OPS CRITICAL ALARM: Found {leaks_found} leaked '{secret_type}' records!\n"
    report += "Exposed Files:\n- " + "\n- ".join(files_affected)
    
    return report

# Simulating hitting the GitHub Search API for 'AKIA'
mock_search_data = {
    "total_count": 2,
    "items": [
        {"path": ".env.backup", "repository": {"name": "frontend-app"}},
        {"path": "tests/aws_mock.py", "repository": {"name": "backend-api"}}
    ]
}

print(scan_for_leaked_secrets(mock_search_data, "AWS IAM Key (AKIA)"))
```

**Output of the script:**
```text
🚨 SEC-OPS CRITICAL ALARM: Found 2 leaked 'AWS IAM Key (AKIA)' records!
Exposed Files:
- frontend-app -> .env.backup
- backend-api -> tests/aws_mock.py
```

---

### Task 4: Auto-assign reviewers based on codeowners or workload

**Why use this logic?** Tagging the same Senior Engineer for 40 PRs a week creates massive bottlenecks. A Python round-robin script scraping the GitLab API can evaluate the current open PR load of a 5-person team natively and automatically assign the review to the person with the fewest open tickets.

**Example Log (Dev Workload Matrix):**
`{"alice": 5, "bob": 1, "charlie": 2}`

**Python Script:**
```python
def assign_reviewer_by_workload(pr_id, current_team_workload_counts):
    # 1. Edge case handling inherently safely
    if not current_team_workload_counts:
         return "AUTOMATION FAULT: No team members available for assignment."
         
    # 2. Sort the dictionary logic to find the engineer with the lowest numerical integer natively
    # sorted() returns a list of tuples like [('bob', 1), ('charlie', 2)]
    sorted_devs = sorted(current_team_workload_counts.items(), key=lambda x: x[1])
    
    # 3. Extract the person at the very top of the list 
    assigned_reviewer = sorted_devs[0][0]
    current_load = sorted_devs[0][1]
    
    # 4. Emulate the API assignment sequence:
    # requests.put(f"api/pullrequests/{pr_id}/reviewers", json={"reviewers": [assigned_reviewer]})
    
    return f"PR #{pr_id} automatically assigned to @{assigned_reviewer} (Currently has {current_load} reviews open)."

# Team member review queues 
workloads = {
    "sarah_lead": 12, # Extremely busy
    "james_dev": 4,
    "mike_junior": 0  # Needs work
}

print(assign_reviewer_by_workload(902, workloads))
```

**Output of the script:**
```text
PR #902 automatically assigned to @mike_junior (Currently has 0 reviews open).
```

---

### Task 5: Create release notes automatically from commit messages

**Why use this logic?** Copy-pasting commit strings into Jira or Confluence is tedious. Python iterating over the `git log` natively (or pulling from the commit API) and splitting them structurally into 'Features' vs 'Fixes' based on keywords generates dynamic, human-readable CHANGELOG.md files.

**Example Log (Commit Array):**
`["feat: added login", "fix: resolved crash"]`

**Python Script:**
```python
def generate_release_notes(commit_array):
    # 1. Structure the categorization bins
    notes = {
        "Features": [],
        "Bug Fixes": [],
        "Other": []
    }
    
    # 2. Iterate against standardized (Conventional Commit) formatting organically
    for commit in commit_array:
        lower_commit = commit.lower()
        if lower_commit.startswith("feat:"):
             notes["Features"].append(commit.replace("feat:", "").strip())
        elif lower_commit.startswith("fix:"):
             notes["Bug Fixes"].append(commit.replace("fix:", "").strip())
        else:
             notes["Other"].append(commit.strip())
             
    # 3. Build the Markdown structural report 
    markdown = "## Release Notes\n\n"
    
    for category, items in notes.items():
        if items:
             markdown += f"### {category}\n"
             for item in items:
                  markdown += f"- {item.capitalize()}\n"
             markdown += "\n"
             
    return markdown.strip()

commits = [
    "feat: added OAuth google login",
    "fix: resolved memory leak in API",
    "docs: updated readme with install config",
    "feat: user avatars now visible"
]

print(generate_release_notes(commits))
```

**Output of the script:**
```markdown
## Release Notes

### Features
- Added oauth google login
- User avatars now visible

### Bug Fixes
- Resolved memory leak in api

### Other
- Docs: updated readme with install config
```

---

### Task 6: Validate Git commit messages against Conventional Commits formatting

**Why use this logic?** If a team uses CI/CD to auto-tag versions based on the aforementioned `feat:` / `fix:` tags natively, someone committing `"Fixed stuff"` absolutely shatters the pipeline. A pre-receive webhook executing Python regex organically blocks the push dynamically.

**Example Log (Regex Pattern check):**
`Pattern: ^(feat|fix|docs|style|refactor|test|chore):\s.+`

**Python Script:**
```python
import re

def pre_receive_commit_validator(commit_message):
    # 1. Establish the explicit Conventional Commits Regex Standard
    # Valid EX: "feat: implemented Stripe" | Invalid EX: "WIP updated stuff"
    pattern = re.compile(r"^(feat|fix|docs|style|refactor|test|chore)(\([a-z0-9\-]+\))?:\s.+")
    
    # 2. Extract evaluation securely
    if pattern.match(commit_message):
         return f"[OK] Commit accepted: '{commit_message}'"
         
    # 3. Halt the execution matrix structurally to reject the push
    error_msg = (
         f"❌ PUSH REJECTED: Commit message '{commit_message}' is invalid.\n"
         f"Must start with: feat:, fix:, docs:, chore:, etc."
    )
    return error_msg

valid_commit = "fix(api): resolved 500 error on checkout"
invalid_commit = "updated the database connection logic"

print(pre_receive_commit_validator(valid_commit))
print(pre_receive_commit_validator(invalid_commit))
```

**Output of the script:**
```text
[OK] Commit accepted: 'fix(api): resolved 500 error on checkout'
❌ PUSH REJECTED: Commit message 'updated the database connection logic' is invalid.
Must start with: feat:, fix:, docs:, chore:, etc.
```

---

### Task 7: Webhook listener for push events (Python FastAPI)

**Why use this logic?** GitLab doesn't inherently notify Jenkin systems dynamically unless explicitly commanded. A 20-line asynchronous FastAPI Python script listening directly for `POST` SCM Webhooks enables you to trigger infinite custom downstream logic the second code merges.

**Example Log (FastAPI POST Payload):**
`{"event_kind": "push", "ref": "refs/heads/main"}`

**Python Script:**
```python
# from fastapi import FastAPI, Request
# app = FastAPI()

def mock_fastapi_webhook_handler(webhook_json_payload):
    # 1. Emulate the API endpoint receiving data: @app.post("/webhook")
    
    # 2. Extract Event rules dynamically based on GitHub/GitLab schemas natively
    event_type = webhook_json_payload.get("event_kind", "unknown")
    branch_ref = webhook_json_payload.get("ref", "")
    author = webhook_json_payload.get("user_name", "Anonymous")
    
    # 3. Route specific logic based upon webhook types natively
    if event_type == "push" and "main" in branch_ref:
         # Trigger Production CI securely
         return f"WEBHOOK ACCEPTED: Push to Main detected from '{author}'. Triggering Production Pipeline!"
         
    elif event_type == "merge_request":
         return f"WEBHOOK ACCEPTED: MR Event received. Triggering Auto-Review Bot!"
         
    else:
         return "WEBHOOK ACCEPTED: Event ignored (Not a main branch push)."

payload = {
    "event_kind": "push", 
    "ref": "refs/heads/main", 
    "user_name": "DevSecOps-Bot"
}

print(mock_fastapi_webhook_handler(payload))
```

**Output of the script:**
```text
WEBHOOK ACCEPTED: Push to Main detected from 'DevSecOps-Bot'. Triggering Production Pipeline!
```

---

### Task 8: Backup repositories locally via Git CLI wrapper

**Why use this logic?** If GitHub goes down, your CI logic drops completely. Python's `subprocess` natively runs `git clone --mirror` commands asynchronously to safely back up 50 organization repositories simultaneously to AWS S3 or a local NAS disk.

**Example Log (Process stack execution):**
`["git", "clone", "--mirror", "https://github..."]`

**Python Script:**
```python
import subprocess

def clone_scm_repositories_locally(repo_url_list, backup_directory):
    # 1. Iterate over massive URL dumps securely
    report = []
    
    for url in repo_url_list:
        # Extract the basic name natively (e.g. 'project.git')
        repo_name = url.split("/")[-1]
        target_path = f"{backup_directory}/{repo_name}"
        
        # 2. Construct Git CLI mirror execution command cleanly
        cmd = ["git", "clone", "--mirror", url, target_path]
        
        # 3. In reality: subprocess.run(cmd, check=True, capture_output=True)
        # We model the successful completion status mathematically
        generated_cmd_string = " ".join(cmd)
        report.append(f"SUCCESS: Executed [ {generated_cmd_string} ]")
        
    return "--- NAS BACKUP SCRIPT ---\n" + "\n".join(report)

repos = [
    "https://gitlab.internal/core/auth-api.git",
    "https://github.com/my-org/frontend-react.git"
]

print(clone_scm_repositories_locally(repos, "/mnt/nas_storage/git_backups"))
```

**Output of the script:**
```text
--- NAS BACKUP SCRIPT ---
SUCCESS: Executed [ git clone --mirror https://gitlab.internal/core/auth-api.git /mnt/nas_storage/git_backups/auth-api.git ]
SUCCESS: Executed [ git clone --mirror https://github.com/my-org/frontend-react.git /mnt/nas_storage/git_backups/frontend-react.git ]
```

---

### Task 9: Sync configuration files across multiple repositories

**Why use this logic?** If you update a `.dockerignore` or `.editorconfig` rule, updating 40 microservices manually is physically impossible. Python clones every repository natively, copies the "Gold Master" file over, commits, and auto-pushes identically across the SCM matrix intelligently.

**Example Log (FileSystem Overwrites):**
`[Overwrite: repoA/.editorconfig ]`

**Python Script:**
```python
def synchronize_global_configuration(target_repos, master_file_name, new_file_content):
    # 1. This function simplifies the exact operational loop executing a GitOps sync sync
    modifications = []
    
    for repo in target_repos:
         # Simulated steps inherently:
         # a) git clone {repo}
         # b) with open(master_file_name, 'w') as f: f.write(new_file_content)
         # c) git commit -am "chore: synced standard config"
         # d) git push
         modifications.append(f"[{repo}] Synced standard '{master_file_name}' and pushed.")
         
    # 2. Present conclusion execution structurally
    return "--- GLOBAL CONFIG SYNC ---\n" + "\n".join(modifications)

repositories = ["auth-service", "billing-service", "inventory-service"]

print(synchronize_global_configuration(repositories, ".dockerignore", "node_modules/\n*.log\n.env"))
```

**Output of the script:**
```text
--- GLOBAL CONFIG SYNC ---
[auth-service] Synced standard '.dockerignore' and pushed.
[billing-service] Synced standard '.dockerignore' and pushed.
[inventory-service] Synced standard '.dockerignore' and pushed.
```

---

### Task 10: Trigger CI/CD pipelines via SCM API endpoints

**Why use this logic?** Sometimes an infrastructure Python script requires Bitbucket Pipelines to execute immediately after modifying a specific database natively. Hitting the SCM's pipeline-trigger API directly ensures asynchronous flows remain completely untouched visually.

**Example Log (API Execution Trigger payloads):**
`{"ref": "master", "variables": {"TARGET": "prod"}}`

**Python Script:**
```python
# import requests 

def trigger_scm_ci_pipeline(scm_provider, project_id, branch_name, variables_dict):
    # 1. Construct generalized execution POST payload structurally
    payload = {
        "ref": branch_name,
        "variables": variables_dict
    }
    
    # 2. Build the provider-specific routing logic
    if scm_provider.lower() == "gitlab":
         endpoint = f"https://gitlab.com/api/v4/projects/{project_id}/pipeline"
    elif scm_provider.lower() == "github": # GitHub Actions Workflow Dispatch
         endpoint = f"https://api.github.com/repos/{project_id}/actions/workflows/main.yml/dispatches"
    else:
         return "Unsupported CI orchestrator natively."
         
    # 3. Simulate execution structurally
    # requests.post(endpoint, json=payload, headers={"Authorization": "Bearer XYZ"})
    
    return f"SCM AUTOMATION: Dispatched Job dynamically to [{endpoint}].\nInjected Runtime Flags: {variables_dict}"

print(trigger_scm_ci_pipeline("gitlab", "490192", "master", {"DEPLOY_ENV": "production", "DEBUG": "false"}))
```

**Output of the script:**
```text
SCM AUTOMATION: Dispatched Job dynamically to [https://gitlab.com/api/v4/projects/490192/pipeline].
Injected Runtime Flags: {'DEPLOY_ENV': 'production', 'DEBUG': 'false'}
```

---

By leveraging Python scripts internally to interact exactly with Git operations and external SCM APIs directly, DevOps architectures replace repetitive human clicks entirely with verifiable mathematical pipelines globally.
