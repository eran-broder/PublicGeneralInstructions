import subprocess
import sys
from functools import partial, reduce
from pathlib import Path

def log_output(message, level="INFO"):
    print(f"[{level}] {message}")
    return message

def run_git_command(cmd, capture_output=True):
    full_cmd = ['git'] + cmd
    log_output(f"Executing: {' '.join(full_cmd)}")
    
    try:
        result = subprocess.run(
            full_cmd, 
            capture_output=capture_output, 
            text=True, 
            cwd=Path.cwd()
        )
        
        if result.stdout:
            log_output(f"STDOUT: {result.stdout.strip()}")
        if result.stderr:
            log_output(f"STDERR: {result.stderr.strip()}", "WARN")
        
        log_output(f"Return code: {result.returncode}")
        
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, full_cmd, result.stdout, result.stderr)
            
        return result
    except subprocess.CalledProcessError as e:
        log_output(f"Command failed: {e}", "ERROR")
        log_output(f"Error output: {e.stderr}", "ERROR")
        raise
    except FileNotFoundError:
        log_output("Git not found in PATH", "ERROR")
        sys.exit(1)

def check_git_status():
    log_output("Checking git status...")
    result = run_git_command(['status', '--porcelain'])
    files = result.stdout.strip().split('\n') if result.stdout.strip() else []
    log_output(f"Found {len(files)} changed files")
    return files

def check_git_repo():
    log_output("Verifying git repository...")
    try:
        run_git_command(['rev-parse', '--git-dir'])
        log_output("Valid git repository confirmed")
        return True
    except subprocess.CalledProcessError:
        log_output("Not a git repository", "ERROR")
        return False

def git_add_all():
    log_output("Adding all files to staging...")
    result = run_git_command(['add', '.'])
    log_output("Files added to staging area")
    return result

def git_commit(message):
    log_output(f"Committing with message: '{message}'")
    try:
        result = run_git_command(['commit', '-m', message])
        log_output("Commit successful")
        return result
    except subprocess.CalledProcessError as e:
        if "nothing to commit" in e.stderr:
            log_output("Nothing to commit, working tree clean", "WARN")
            return None
        raise

def git_push(remote="origin", branch=None):
    if not branch:
        branch_result = run_git_command(['branch', '--show-current'])
        branch = branch_result.stdout.strip()
    
    log_output(f"Pushing to {remote}/{branch}...")
    result = run_git_command(['push', remote, branch])
    log_output("Push successful")
    return result

def get_commit_hash():
    result = run_git_command(['rev-parse', 'HEAD'])
    commit_hash = result.stdout.strip()[:8]
    log_output(f"Latest commit: {commit_hash}")
    return commit_hash

def validate_remote_connection(remote="origin"):
    log_output(f"Validating remote '{remote}' connection...")
    try:
        run_git_command(['ls-remote', remote, '--exit-code'])
        log_output("Remote connection validated")
        return True
    except subprocess.CalledProcessError:
        log_output(f"Cannot connect to remote '{remote}'", "ERROR")
        return False

def auto_git_workflow(commit_message="Auto commit", remote="origin"):
    log_output("Starting automated git workflow...")
    
    workflow_steps = [
        ("Repository validation", lambda: check_git_repo()),
        ("Status check", lambda: check_git_status()),
        ("Remote validation", lambda: validate_remote_connection(remote)),
        ("Add files", git_add_all),
        ("Commit changes", lambda: git_commit(commit_message)),
        ("Push changes", lambda: git_push(remote)),
        ("Get final commit", get_commit_hash)
    ]
    
    results = {}
    
    for step_name, step_func in workflow_steps:
        log_output(f"Step: {step_name}")
        try:
            result = step_func()
            results[step_name] = result
            
            if step_name == "Repository validation" and not result:
                log_output("Workflow aborted: Not a git repository", "ERROR")
                return results
                
            if step_name == "Remote validation" and not result:
                log_output("Workflow aborted: Remote connection failed", "ERROR")
                return results
                
            if step_name == "Status check" and not result:
                log_output("No changes detected", "WARN")
                
        except Exception as e:
            log_output(f"Step '{step_name}' failed: {e}", "ERROR")
            results[step_name] = None
            if step_name in ["Add files", "Commit changes", "Push changes"]:
                log_output("Workflow aborted due to critical error", "ERROR")
                break
    
    log_output("Git workflow completed")
    return results

def debug_git_environment():
    log_output("=== Git Environment Debug Info ===")
    
    debug_commands = [
        (['--version'], "Git version"),
        (['config', '--get', 'user.name'], "User name"),
        (['config', '--get', 'user.email'], "User email"),
        (['remote', '-v'], "Remote repositories"),
        (['branch', '-a'], "All branches"),
        (['log', '--oneline', '-5'], "Recent commits")
    ]
    
    for cmd, description in debug_commands:
        try:
            log_output(f"Checking: {description}")
            run_git_command(cmd)
        except subprocess.CalledProcessError as e:
            log_output(f"Could not get {description.lower()}: {e}", "WARN")

if __name__ == "__main__":
    debug_git_environment()
    auto_git_workflow("Add new files and changes")
