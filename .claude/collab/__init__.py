"""
Claude Collab - Inter-Claude Collaboration for Medieval Trading Game
====================================================================

Unity Supervisor Module - Coordinates AI workers through ClaudeColab

Quick Usage:
    from collab import brain, tasks, colab, supervisor

    # SUPERVISOR MODE (Unity coordinates all workers)
    supervisor.start_session()      # Connect, sync, announce
    supervisor.team_status()        # Check all workers
    supervisor.assign_task(...)     # Assign work to workers
    supervisor.announce_push(...)   # Announce git pushes
    supervisor.end_session()        # Close session

    # Share knowledge with the team
    brain.learn("Discovered that X pattern works well for Y")
    brain.snippet("def foo(): pass", "python", "description")
    colab.share("Knowledge", tags=['medieval-game'])

    # Task management
    colab.post_task("Do this", to_claude="BLACK", priority=5)
    colab.get_tasks('pending')
    colab.claim_task(task_id)
    colab.complete_task(task_id, "Done!")

    # Chat with team
    colab.chat("Team update message")
    colab.get_chat(20)

    # Work logging
    colab.log_work("action", {"details": "..."})
"""

from .shared_brain import brain, SharedBrain
from .shared_tasks import tasks, SharedTasks
from .claude_collab import colab, ClaudeCollab
from .supervisor_sync import supervisor, SupervisorSync

__all__ = [
    'brain', 'tasks', 'colab', 'supervisor',
    'SharedBrain', 'SharedTasks', 'ClaudeCollab', 'SupervisorSync'
]

# Quick access functions
def learn(lesson, tags=None):
    """Quick share a lesson learned"""
    return brain.learn(lesson, tags)

def discover(discovery, tags=None):
    """Quick share a discovery"""
    return brain.discover(discovery, tags)

def snippet(code, language, description=None, tags=None):
    """Quick share a code snippet"""
    return brain.snippet(code, language, description, tags)

def post_task(task, to_claude=None, task_type=None, priority=5):
    """Quick post a task"""
    return tasks.post(task, to_claude, task_type, priority)

def check_tasks():
    """Check for pending tasks assigned to me"""
    return tasks.pending()

def from_rev():
    """Get recent knowledge from Rev's Claude (R)"""
    return brain.from_other()

def stats():
    """Get collaboration statistics"""
    return {
        "brain": brain.stats(),
        "tasks": tasks.stats()
    }
