import os
import sys
import time
import json
import subprocess
import requests
import tempfile
import logging
from datetime import datetime
import traceback
import importlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("aiter_api_watcher.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("aiter_api_watcher")

# Configuration file path
CONFIG_FILE = "aiter_api_watcher_config.json"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
NOTIFICATION_REPO = "EmbeddedLLM/aiter-api-watcher"
CHECK_INTERVAL = 3600  # Check every hour by default

def load_config():
    """Load configuration from JSON file"""
    if not os.path.exists(CONFIG_FILE):
        default_config = {
            "functions_to_monitor": [
                {
                    "import_statement": "import aiter.fused_moe_bf16_asm as rocm_aiter_asm_fmoe",
                    "function_path": "rocm_aiter_asm_fmoe.moe_sorting_ck"
                },
                {
                    "import_statement": "import aiter.fused_moe_bf16_asm as rocm_aiter_asm_fmoe",
                    "function_path": "rocm_aiter_asm_fmoe.asm_moe"
                },
                {
                    "import_statement": "from aiter.fused_moe_bf16_asm import ck_moe_2stages",
                    "function_path": "ck_moe_2stages"
                }
            ],
            "check_interval_seconds": CHECK_INTERVAL,
            "last_checked_commit": "",
            "start_commit": "",  # User can specify which commit to start with
            "repository_url": "https://github.com/ROCm/aiter.git",
            "commit_list": [],
            "compare_pair": []
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=2)
        return default_config

    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config):
    """Save configuration to JSON file"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def get_latest_commit(repo_url):
    """Get the latest commit hash from the repository"""
    try:
        result = subprocess.run(
            ["git", "ls-remote", repo_url, "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        commit_hash = result.stdout.split()[0]
        return commit_hash
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get latest commit: {e}")
        return None

def create_github_issue(title, body):
    """Create a GitHub issue to notify about API changes"""
    if not GITHUB_TOKEN:
        logger.error("GitHub token not set. Cannot create issue.")
        return False

    url = f"https://api.github.com/repos/{NOTIFICATION_REPO}/issues"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "title": title,
        "body": body
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 201:
        logger.info(f"GitHub issue created successfully: {response.json()['html_url']}")
        return True
    else:
        logger.error(f"Failed to create GitHub issue: {response.status_code}, {response.text}")
        return False

def get_commit_history(repo_dir, start_commit=None):
    """Get the commit history from the repository"""
    if start_commit:
        cmd = ["git", "log", "--format=%H", f"{start_commit}..HEAD"]
    else:
        cmd = ["git", "log", "--format=%H"]

    result = subprocess.run(cmd, cwd=repo_dir, capture_output=True, text=True, check=True)
    commits = result.stdout.strip().split('\n')
    return [c for c in commits if c]  # Filter out empty strings

def get_commit_info(repo_dir, commit):
    """Get commit information (author, date, message)"""
    cmd = ["git", "show", "-s", "--format=%an|%ae|%ad|%s", commit]
    result = subprocess.run(cmd, cwd=repo_dir, capture_output=True, text=True, check=True)
    parts = result.stdout.strip().split('|', 3)
    if len(parts) == 4:
        return {
            "author_name": parts[0],
            "author_email": parts[1],
            "date": parts[2],
            "message": parts[3]
        }
    return {"message": "Commit info not available"}
def check_function_in_subprocess(temp_dir, import_statement, function_path):
    """Run function check in a separate process to ensure clean environment"""
    # Extract the function name from the path
    function_name = function_path.split('.')[-1]

    # Create a temporary Python script to check the function
    script_content = f"""
import os
import sys
import inspect
import json
import traceback

# Add the temp directory to sys.path
sys.path.insert(0, "{temp_dir}")

result = {{
    "exists": False,
    "signature": None,
    "parameters": None,
    "source": None,
    "error": None
}}

try:
    # Execute the import statement exactly as provided
    {import_statement}

    # Access the function directly by name as it was imported
    function = {function_path}

    # Get the signature
    signature = inspect.signature(function)
    result["signature"] = str(signature)

    # Extract detailed parameter information
    params = []
    for name, param in signature.parameters.items():
        param_info = {{
            "name": name,
            "kind": str(param.kind),
            "default": "NO_DEFAULT" if param.default is inspect.Parameter.empty else repr(param.default),
            "annotation": "NO_ANNOTATION" if param.annotation is inspect.Parameter.empty else str(param.annotation)
        }}
        params.append(param_info)

    result["parameters"] = params

    # Get function source if possible
    try:
        source = inspect.getsource(function)
        result["source"] = source
    except (TypeError, OSError):
        result["source"] = "Source code not available"

    result["exists"] = True
except Exception as e:
    result["error"] = f"{{type(e).__name__}}: {{str(e)}}\\n{{traceback.format_exc()}}"

# Print the result as JSON with a special marker to identify it
print("JSON_RESULT_START")
print(json.dumps(result))
print("JSON_RESULT_END")
"""

    # Write the script to a temporary file
    script_path = os.path.join(temp_dir, "check_function.py")
    with open(script_path, 'w') as f:
        f.write(script_content)

    # Run the script in a separate process
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            check=False  # Don't raise an exception on non-zero exit code
        )

        if result.returncode != 0:
            return {
                "exists": False,
                "signature": None,
                "parameters": None,
                "source": None,
                "error": f"Script exited with code {result.returncode}\nStdout: {result.stdout}\nStderr: {result.stderr}"
            }

        # Extract the JSON part from the output using markers
        stdout = result.stdout
        try:
            start_marker = "JSON_RESULT_START"
            end_marker = "JSON_RESULT_END"

            start_idx = stdout.find(start_marker)
            end_idx = stdout.find(end_marker)

            if start_idx == -1 or end_idx == -1:
                # If markers not found, try to find JSON directly as a fallback
                json_start = stdout.find("{")
                json_end = stdout.rfind("}") + 1

                if json_start != -1 and json_end > json_start:
                    json_str = stdout[json_start:json_end]
                else:
                    raise ValueError("Could not find JSON output in script result")
            else:
                # Extract the JSON between markers
                json_str = stdout[start_idx + len(start_marker):end_idx].strip()

            return json.loads(json_str)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error parsing script output: {e}")
            logger.debug(f"Script stdout: {stdout}")
            return {
                "exists": False,
                "signature": None,
                "parameters": None,
                "source": None,
                "error": f"Failed to parse JSON output: {str(e)}\nOutput: {stdout}"
            }
    except Exception as e:
        return {
            "exists": False,
            "signature": None,
            "parameters": None,
            "source": None,
            "error": f"Error running check script: {str(e)}"
        }


def compare_parameters(prev_params, curr_params):
    """Compare function parameters and return detailed changes"""
    if prev_params is None or curr_params is None:
        return "Cannot compare parameters (one or both are missing)"

    changes = []

    # Find removed parameters
    prev_param_names = {p["name"] for p in prev_params}
    curr_param_names = {p["name"] for p in curr_params}

    removed = prev_param_names - curr_param_names
    if removed:
        changes.append(f"Removed parameters: {', '.join(removed)}")

    # Find added parameters
    added = curr_param_names - prev_param_names
    if added:
        changes.append(f"Added parameters: {', '.join(added)}")

    # Check for changes in existing parameters
    for prev_param in prev_params:
        name = prev_param["name"]
        if name in curr_param_names:
            curr_param = next(p for p in curr_params if p["name"] == name)

            # Check for changes in parameter properties
            param_changes = []

            if prev_param["kind"] != curr_param["kind"]:
                param_changes.append(f"kind changed from {prev_param['kind']} to {curr_param['kind']}")

            if prev_param["default"] != curr_param["default"]:
                param_changes.append(f"default value changed from {prev_param['default']} to {curr_param['default']}")

            if prev_param["annotation"] != curr_param["annotation"]:
                param_changes.append(f"type annotation changed from {prev_param['annotation']} to {curr_param['annotation']}")

            if param_changes:
                changes.append(f"Parameter '{name}' changed: {'; '.join(param_changes)}")

    # Check for reordering of parameters
    prev_ordered_names = [p["name"] for p in prev_params if p["name"] in curr_param_names]
    curr_ordered_names = [p["name"] for p in curr_params if p["name"] in prev_param_names]

    if prev_ordered_names != curr_ordered_names:
        changes.append(f"Parameter order changed: {' -> '.join([', '.join(prev_ordered_names), ', '.join(curr_ordered_names)])}")

    return changes if changes else ["No parameter changes detected"]

def compare_two_commits(config, old_commit, new_commit):
    """Compare two specific commits"""
    with tempfile.TemporaryDirectory() as temp_dir:
        subprocess.run(["git", "clone", config["repository_url"], temp_dir], check=True)

        # Checkout old commit
        subprocess.run(["git", "checkout", old_commit], cwd=temp_dir, check=True)
        subprocess.run(["git", "submodule", "update", "--init", "--recursive"], cwd=temp_dir, check=True)
        subprocess.run([sys.executable, "setup.py", "develop"], cwd=temp_dir, check=True)

        old_signatures = {}
        for func_config in config["functions_to_monitor"]:
            old_signatures[func_config["function_path"]] = check_function_in_subprocess(
                temp_dir, func_config["import_statement"], func_config["function_path"]
            )

        # Checkout new commit
        subprocess.run(["git", "checkout", new_commit], cwd=temp_dir, check=True)
        subprocess.run(["git", "submodule", "update", "--init", "--recursive"], cwd=temp_dir, check=True)
        subprocess.run([sys.executable, "setup.py", "develop"], cwd=temp_dir, check=True)

        for func_config in config["functions_to_monitor"]:
            new_signature = check_function_in_subprocess(
                temp_dir, func_config["import_statement"], func_config["function_path"]
            )

            old_signature = old_signatures.get(func_config["function_path"], {})

            if (old_signature.get("exists") != new_signature.get("exists") or
                old_signature.get("signature") != new_signature.get("signature")):

                param_changes = compare_parameters(
                    old_signature.get("parameters"),
                    new_signature.get("parameters")
                )

                title = f"API Change Detected (Compare Mode): {func_config['function_path']}"
                body = f"""## API Change Detected (Compare Mode)

Function: `{func_config['function_path']}`
Import: `{func_config['import_statement']}`
Old Commit: {old_commit}
New Commit: {new_commit}

### Old Signature
{old_signature.get('signature', 'N/A')}

### New Signature
{new_signature.get('signature', 'N/A')}

### Parameter Changes
{chr(10).join(f"- {change}" for change in param_changes)}

### Error (if any)
```
{new_signature.get('error', 'No error')}
```
"""
                create_github_issue(title, body)
            else:
                logger.info(f"No API change for {func_config['function_path']} between {old_commit} and {new_commit}")


def process_commit_list(config):
    """Process a list of commits in order"""
    commit_list = config["commit_list"]

    if not commit_list:
        logger.info("No commits specified in commit_list")
        return

    with tempfile.TemporaryDirectory() as temp_dir:
        subprocess.run(["git", "clone", config["repository_url"], temp_dir], check=True)

        # Process commits in order
        for commit in commit_list:
            logger.info(f"Processing commit {commit}")
            try:
                subprocess.run(["git", "checkout", commit], cwd=temp_dir, check=True)
                subprocess.run(["git", "submodule", "update", "--init", "--recursive"], cwd=temp_dir, check=True)
                subprocess.run([sys.executable, "setup.py", "develop"], cwd=temp_dir, check=True)

                for func_config in config["functions_to_monitor"]:
                    import_statement = func_config["import_statement"]
                    function_path = func_config["function_path"]

                    current_signature = check_function_in_subprocess(
                        temp_dir, import_statement, function_path
                    )

                    previous_signature = func_config.get("last_signature", {})

                    if not previous_signature:
                        func_config["last_signature"] = current_signature
                        logger.info(f"Initial signature for {function_path}: {current_signature.get('signature', 'Not available')}")
                    elif (previous_signature.get("exists") != current_signature["exists"] or
                          previous_signature.get("signature") != current_signature["signature"]):

                        param_changes = compare_parameters(
                            previous_signature.get("parameters"),
                            current_signature.get("parameters")
                        )

                        title = f"API Change Detected: {function_path}"
                        body = f"""## API Change Detected

Function: `{function_path}`
Import: `{import_statement}`
Commit: {commit}

### Previous State
{previous_signature.get('signature', 'N/A')}

### Current State
{current_signature.get('signature', 'N/A')}

### Parameter Changes
{chr(10).join(f"- {change}" for change in param_changes)}

### Error (if any)
```
{current_signature.get('error', 'No error')}
```
"""
                        create_github_issue(title, body)

                        func_config["last_signature"] = current_signature
                        logger.info(f"API change detected for {function_path}")
                    else:
                        logger.info(f"No API change for {function_path}")

            except Exception as e:
                logger.error(f"Error processing commit {commit}: {e}")
                logger.error(traceback.format_exc())

        # After processing, clear commit_list and continue normal monitoring
        config["commit_list"] = []
        save_config(config)
        logger.info("Finished processing commit list. Resuming normal monitoring.")


def check_api_changes(config):
    """Check for API changes in the monitored functions"""

    # Mode 3: Compare two specific commits
    if config.get("compare_pair"):
        old_commit, new_commit = config["compare_pair"]
        logger.info(f"Comparing two commits: {old_commit} -> {new_commit}")
        compare_two_commits(config, old_commit, new_commit)
        return 3

    # Mode 2: Process a list of commits
    if config.get("commit_list"):
        logger.info(f"Processing specified commit list: {config['commit_list']}")
        process_commit_list(config)
        return 2

    # Default Mode 1: Monitor latest commits
    latest_commit = get_latest_commit(config["repository_url"])

    if not latest_commit:
        logger.error("Failed to get latest commit")
        return

    # If we've already checked this commit, skip
    if config["last_checked_commit"] == latest_commit:
        logger.info(f"No new commits since last check ({latest_commit})")
        return

    # Create a temporary directory for the repository
    with tempfile.TemporaryDirectory() as temp_dir:
        # Clone the repository to get commit history
        subprocess.run(["git", "clone", config["repository_url"], temp_dir], check=True)

        # Get commit history
        start_commit = config.get("start_commit") or config.get("last_checked_commit")
        if start_commit:
            commits = get_commit_history(temp_dir, start_commit)
            logger.info(f"Found {len(commits)} new commits since {start_commit}")
        else:
            # If no start commit is specified, just check the latest
            commits = [latest_commit]
            logger.info(f"Checking only the latest commit {latest_commit}")

        # Process each commit in chronological order (oldest first)
        commits.reverse()

        for commit in commits:
            logger.info(f"Checking commit {commit}")
            commit_info = get_commit_info(temp_dir, commit)

            # Create a new temporary directory for this commit
            with tempfile.TemporaryDirectory() as commit_temp_dir:
                try:
                    # Clone the repository for this specific commit
                    logger.info(f"Cloning repository for commit {commit}")
                    subprocess.run(["git", "clone", "--recursive", config["repository_url"], commit_temp_dir], check=True)

                    # Checkout the specific commit
                    logger.info(f"Checking out commit {commit}")
                    subprocess.run(["git", "checkout", commit], cwd=commit_temp_dir, check=True)

                    # Update submodules
                    logger.info("Updating submodules")
                    subprocess.run(["git", "submodule", "sync"], cwd=commit_temp_dir, check=True)
                    subprocess.run(["git", "submodule", "update", "--init", "--recursive"], cwd=commit_temp_dir, check=True)

                    # Install aiter
                    logger.info("Installing aiter package")
                    try:
                        subprocess.run([sys.executable, "setup.py", "develop"], cwd=commit_temp_dir, check=True)
                        logger.info("Successfully installed aiter")
                    except subprocess.CalledProcessError as e:
                        logger.warning(f"Installation had issues, but continuing: {e}")

                    # Check each function
                    for func_config in config["functions_to_monitor"]:
                        import_statement = func_config["import_statement"]
                        function_path = func_config["function_path"]

                        # Get the current signature using a separate process
                        current_signature = check_function_in_subprocess(
                            commit_temp_dir, 
                            import_statement, 
                            function_path
                        )

                        # Compare with the previous signature if it exists
                        previous_signature = func_config.get("last_signature", {})

                        if not previous_signature:
                            # First time checking this function
                            func_config["last_signature"] = current_signature
                            logger.info(f"Initial signature for {function_path}: {current_signature.get('signature', 'Not available')}")
                        elif (previous_signature.get("exists") != current_signature["exists"] or
                              previous_signature.get("signature") != current_signature["signature"]):

                            # Analyze parameter changes in detail
                            param_changes = compare_parameters(
                                previous_signature.get("parameters"), 
                                current_signature.get("parameters")
                            )

                            # API has changed, create a GitHub issue
                            title = f"API Change Detected: {function_path}"

                            body = f"""## API Change Detected

Function: `{function_path}`
Import: `{import_statement}`
Commit: [{commit}](https://github.com/ROCm/aiter/commit/{commit})
Date: {commit_info.get('date', 'Unknown')}
Author: {commit_info.get('author_name', 'Unknown')} <{commit_info.get('author_email', '')}>
Message: {commit_info.get('message', 'No message')}

### Previous State
Existed: {previous_signature.get('exists', False)}
Signature: `{previous_signature.get('signature', 'N/A')}`

### Current State
Exists: {current_signature['exists']}
Signature: `{current_signature.get('signature', 'N/A')}`

### Parameter Changes
{chr(10).join(f"- {change}" for change in param_changes)}

### Error (if any)
```
{current_signature.get('error', 'No error')}
```
"""
                            create_github_issue(title, body)

                            # Update the signature
                            func_config["last_signature"] = current_signature
                            logger.info(f"API change detected for {function_path}")
                        else:
                            logger.info(f"No API change for {function_path}")

                except Exception as e:
                    logger.error(f"Error processing commit {commit}: {e}")
                    logger.error(traceback.format_exc())

        # Update the last checked commit
        config["last_checked_commit"] = latest_commit
        save_config(config)
        logger.info(f"Updated last checked commit to {latest_commit}")

def main_loop():
    """Main loop to periodically check for API changes"""
    config = load_config()
    check_interval = config.get("check_interval_seconds", CHECK_INTERVAL)

    logger.info("Starting aiter API watcher")
    logger.info(f"Monitoring {len(config['functions_to_monitor'])} functions")
    logger.info(f"Check interval: {check_interval} seconds")

    while True:
        try:
            logger.info("Checking for API changes...")
            mode = check_api_changes(config)
            if mode == 3:
                logger.info("Exiting after comparing two commits")
                break
            logger.info(f"Next check in {check_interval} seconds")
            time.sleep(check_interval)
        except KeyboardInterrupt:
            logger.info("Stopping aiter API watcher")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            logger.error(traceback.format_exc())
            # Wait a bit before retrying
            time.sleep(60)

if __name__ == "__main__":
    main_loop()