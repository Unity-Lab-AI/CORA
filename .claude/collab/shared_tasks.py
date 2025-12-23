"""
Shared Tasks - Claude-to-Claude Task Coordination
==================================================
A distributed task queue between Rev's Claude and G14's Claude.

Usage:
    from shared_tasks import tasks

    # Post a task for the other Claude
    tasks.post("Review this code snippet", task_type="code_review")
    tasks.post("Research Python async patterns", to_claude="G", priority=3)

    # Check for tasks assigned to me
    my_tasks = tasks.pending()

    # Claim and work on a task
    task = tasks.claim(task_id)
    # ... do the work ...
    tasks.complete(task_id, result="Here's what I found...")

    # Or mark as failed
    tasks.fail(task_id, error="Couldn't access the resource")
"""

import os
import requests
from datetime import datetime

# Supabase config - env vars with fallback to hardcoded (for backwards compatibility)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://yjyryzlbkbtdzguvqegt.supabase.co")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlqeXJ5emxia2J0ZHpndXZxZWd0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk0NTMzOTYsImV4cCI6MjA3NTAyOTM5Nn0.Vujw3q9_iHj4x5enf42V-7g355Tnzp9zdsoNYVCV8TY")

# Author identifier - env var or default to R (Rev's Claude). G14's Claude should set CLAUDE_AUTHOR=G
AUTHOR = os.environ.get("CLAUDE_AUTHOR", "R")

class SharedTasks:
    def __init__(self, author=AUTHOR):
        self.author = author
        self.base_url = f"{SUPABASE_URL}/rest/v1/shared_tasks"
        self.headers = {
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    def post(self, task, to_claude=None, task_type=None, priority=5):
        """Post a task for another Claude (or any Claude if to_claude is None).

        Args:
            task: Description of what needs to be done
            to_claude: "R", "G", or None (anyone can claim)
            task_type: Category like "code_review", "research", "build", "test"
            priority: 1=urgent, 5=normal, 10=low

        Returns:
            The created task or error dict
        """
        data = {
            "from_claude": self.author,
            "to_claude": to_claude,
            "task": task,
            "task_type": task_type,
            "priority": priority,
            "status": "pending"
        }

        try:
            resp = requests.post(self.base_url, json=data, headers=self.headers, timeout=10)
            if resp.status_code == 201:
                result = resp.json()
                print(f"Posted task: {task[:50]}... (priority={priority})")
                return result[0] if result else {"status": "posted"}
            else:
                return {"error": resp.text, "status_code": resp.status_code}
        except Exception as e:
            return {"error": str(e)}

    def pending(self, for_me=True):
        """Get pending tasks.

        Args:
            for_me: If True, only tasks assigned to me or anyone (to_claude is null)
                   If False, all pending tasks
        """
        try:
            url = f"{self.base_url}?status=eq.pending&order=priority.asc,created_at.asc"
            if for_me:
                # Tasks for me specifically OR tasks for anyone (to_claude is null)
                url = f"{self.base_url}?status=eq.pending&or=(to_claude.eq.{self.author},to_claude.is.null)&order=priority.asc,created_at.asc"

            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            return {"error": resp.text}
        except Exception as e:
            return {"error": str(e)}

    def claim(self, task_id):
        """Claim a task to work on it.

        Args:
            task_id: UUID of the task to claim

        Returns:
            Updated task or error
        """
        data = {
            "status": "claimed",
            "claimed_by": self.author,
            "claimed_at": datetime.utcnow().isoformat()
        }

        try:
            url = f"{self.base_url}?id=eq.{task_id}"
            resp = requests.patch(url, json=data, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                result = resp.json()
                print(f"Claimed task {task_id[:8]}...")
                return result[0] if result else {"status": "claimed"}
            else:
                return {"error": resp.text, "status_code": resp.status_code}
        except Exception as e:
            return {"error": str(e)}

    def start(self, task_id):
        """Mark a task as in_progress."""
        data = {"status": "in_progress"}

        try:
            url = f"{self.base_url}?id=eq.{task_id}"
            resp = requests.patch(url, json=data, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                return resp.json()[0] if resp.json() else {"status": "in_progress"}
            return {"error": resp.text}
        except Exception as e:
            return {"error": str(e)}

    def complete(self, task_id, result=None):
        """Mark a task as completed with optional result.

        Args:
            task_id: UUID of the task
            result: Output/findings from the task
        """
        data = {
            "status": "done",
            "result": result,
            "completed_at": datetime.utcnow().isoformat()
        }

        try:
            url = f"{self.base_url}?id=eq.{task_id}"
            resp = requests.patch(url, json=data, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                print(f"Completed task {task_id[:8]}...")
                return resp.json()[0] if resp.json() else {"status": "done"}
            return {"error": resp.text}
        except Exception as e:
            return {"error": str(e)}

    def fail(self, task_id, error=None):
        """Mark a task as failed.

        Args:
            task_id: UUID of the task
            error: Error message explaining the failure
        """
        data = {
            "status": "failed",
            "error": error,
            "completed_at": datetime.utcnow().isoformat()
        }

        try:
            url = f"{self.base_url}?id=eq.{task_id}"
            resp = requests.patch(url, json=data, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                print(f"Failed task {task_id[:8]}...")
                return resp.json()[0] if resp.json() else {"status": "failed"}
            return {"error": resp.text}
        except Exception as e:
            return {"error": str(e)}

    def get(self, task_id):
        """Get a specific task by ID."""
        try:
            url = f"{self.base_url}?id=eq.{task_id}"
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                result = resp.json()
                return result[0] if result else {"error": "Not found"}
            return {"error": resp.text}
        except Exception as e:
            return {"error": str(e)}

    def from_other(self, status=None):
        """Get tasks posted by the other Claude.

        Args:
            status: Filter by status (pending, claimed, done, failed) or None for all
        """
        other = "G" if self.author == "R" else "R"
        try:
            url = f"{self.base_url}?from_claude=eq.{other}&order=created_at.desc"
            if status:
                url += f"&status=eq.{status}"
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            return {"error": resp.text}
        except Exception as e:
            return {"error": str(e)}

    def my_posts(self, status=None):
        """Get tasks I've posted."""
        try:
            url = f"{self.base_url}?from_claude=eq.{self.author}&order=created_at.desc"
            if status:
                url += f"&status=eq.{status}"
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            return {"error": resp.text}
        except Exception as e:
            return {"error": str(e)}

    def stats(self):
        """Get task queue statistics."""
        try:
            url = f"{self.base_url}?order=created_at.desc&limit=1000"
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                all_tasks = resp.json()

                by_status = {}
                for t in all_tasks:
                    s = t.get('status', 'unknown')
                    by_status[s] = by_status.get(s, 0) + 1

                from_r = len([t for t in all_tasks if t.get('from_claude') == 'R'])
                from_g = len([t for t in all_tasks if t.get('from_claude') == 'G'])

                return {
                    "total": len(all_tasks),
                    "from_R": from_r,
                    "from_G": from_g,
                    "by_status": by_status
                }
            return {"error": resp.text}
        except Exception as e:
            return {"error": str(e)}

    # Handler registry for auto-polling
    _handlers = {}

    @classmethod
    def register_handler(cls, task_type, handler_func):
        """Register a handler function for a task type.

        Args:
            task_type: Type like "code_review", "research", "build"
            handler_func: Function that takes task dict, returns result string

        Example:
            def my_review(task):
                code = task.get('task')
                return f"Reviewed: {code[:100]}..."

            tasks.register_handler("code_review", my_review)
        """
        cls._handlers[task_type] = handler_func
        print(f"Registered handler for '{task_type}'")

    def process_task(self, task):
        """Process a single task using registered handler.

        Args:
            task: Task dict from pending()

        Returns:
            Result from handler or error
        """
        task_id = task.get('id')
        task_type = task.get('task_type', 'default')

        # Claim the task
        self.claim(task_id)
        self.start(task_id)

        try:
            # Find handler
            handler = self._handlers.get(task_type) or self._handlers.get('default')

            if handler:
                result = handler(task)
                self.complete(task_id, result=str(result))
                return {"status": "completed", "task_id": task_id, "result": result}
            else:
                error = f"No handler registered for task_type '{task_type}'"
                self.fail(task_id, error=error)
                return {"status": "failed", "task_id": task_id, "error": error}

        except Exception as e:
            error = f"Handler error: {str(e)}"
            self.fail(task_id, error=error)
            return {"status": "failed", "task_id": task_id, "error": error}

    def poll_once(self):
        """Check for pending tasks and process one.

        Returns:
            Result dict or None if no tasks
        """
        pending = self.pending()
        if not pending or isinstance(pending, dict):
            return None

        # Sort by priority (lower = more urgent)
        pending.sort(key=lambda t: t.get('priority', 5))

        # Process highest priority task
        task = pending[0]
        return self.process_task(task)

    def poll(self, interval=300, max_iterations=None, callback=None):
        """Poll for tasks continuously.

        Args:
            interval: Seconds between checks (default 5 min)
            max_iterations: Stop after N iterations (None = forever)
            callback: Optional function called after each poll with result

        Returns:
            List of results if max_iterations set, else runs forever
        """
        import time

        results = []
        iteration = 0

        print(f"Starting task poll (interval={interval}s)...")

        while max_iterations is None or iteration < max_iterations:
            iteration += 1

            result = self.poll_once()

            if result:
                results.append(result)
                print(f"Processed task: {result.get('status')} - {result.get('task_id', '')[:8]}")

                if callback:
                    callback(result)
            else:
                print(f"No pending tasks (check {iteration})")

            if max_iterations and iteration >= max_iterations:
                break

            time.sleep(interval)

        return results


# Singleton instance
tasks = SharedTasks()


def notify_discord(result):
    """Callback to post task results to Discord channel.

    Usage:
        tasks.poll(callback=notify_discord)
    """
    try:
        import sys
        sys.path.insert(0, '.')
        from me import me

        status = result.get('status', 'unknown')
        task_id = result.get('task_id', '')[:8]
        task_result = result.get('result', result.get('error', 'No details'))

        if len(str(task_result)) > 100:
            task_result = str(task_result)[:100] + '...'

        msg = f"Task {task_id} {status}: {task_result}"
        me.claude_say(msg)
        print(f"Notified Discord: {msg[:50]}...")

    except Exception as e:
        print(f"Discord notify failed: {e}")


if __name__ == "__main__":
    print("Shared Tasks module - waiting for table creation")
    print("Run migrations/shared_tasks_table.sql in Supabase first")

    # Test connection (will fail until table exists)
    stats = tasks.stats()
    print(f"Stats: {stats}")
