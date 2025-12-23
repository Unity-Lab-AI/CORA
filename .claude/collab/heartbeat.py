"""
Heartbeat System for ClaudeColab Supervisor

Checks all 5 channels at regular intervals to stay responsive.
Run this every 1-2 minutes during active supervision.

Usage:
    from heartbeat import heartbeat, start_monitoring

    # Single heartbeat check
    results = heartbeat()

    # Or get formatted report
    report = heartbeat_report()
"""

import sys
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import colab
sys.path.insert(0, '.')
try:
    import importlib
    import claude_colab
    importlib.reload(claude_colab)
    from claude_colab import colab
except ImportError:
    from claude_colab import colab

API_KEY = 'cc_rajMQjFxWP5LeMJzP9BI2R1jmRLSgL'
PROJECT = 'cora'

# Track last heartbeat
_last_heartbeat = None
_heartbeat_interval = 90  # seconds (1.5 minutes)


def ensure_connected() -> bool:
    """Ensure we're connected to ClaudeColab"""
    if not colab.connected:
        colab.connect(API_KEY)
        colab.set_project(PROJECT)
    return colab.connected


def heartbeat() -> Dict[str, Any]:
    """
    Check all 5 channels and return status.

    Returns dict with:
        - timestamp: when check ran
        - connected: bool
        - channels: dict of channel statuses
        - new_items: dict of new items per channel
        - needs_attention: list of things needing response
    """
    global _last_heartbeat

    if not ensure_connected():
        return {"connected": False, "error": "Failed to connect"}

    results = {
        "timestamp": datetime.now().isoformat(),
        "connected": True,
        "channels": {},
        "new_items": {},
        "needs_attention": []
    }

    # 1. CHECK TASKS
    try:
        pending = colab.get_tasks('pending')
        claimed = colab.get_tasks('claimed')
        my_tasks = [t for t in pending if t.get('to_claude') == 'Unity']
        results["channels"]["tasks"] = True
        results["new_items"]["pending_tasks"] = len(pending)
        results["new_items"]["claimed_tasks"] = len(claimed)
        results["new_items"]["tasks_for_me"] = len(my_tasks)
        if my_tasks:
            results["needs_attention"].append(f"{len(my_tasks)} tasks assigned to Unity")
    except Exception as e:
        results["channels"]["tasks"] = False
        results["needs_attention"].append(f"Tasks channel error: {e}")

    # 2. CHECK KNOWLEDGE/BRAIN
    try:
        recent = colab.get_recent(10)
        results["channels"]["knowledge"] = True
        results["new_items"]["recent_knowledge"] = len(recent)
    except Exception as e:
        results["channels"]["knowledge"] = False
        results["needs_attention"].append(f"Knowledge channel error: {e}")

    # 3. CHECK CHAT
    try:
        chat = colab.get_chat(20)
        results["channels"]["chat"] = True
        results["new_items"]["chat_messages"] = len(chat)
    except Exception as e:
        results["channels"]["chat"] = False
        results["needs_attention"].append(f"Chat channel error: {e}")

    # 4. CHECK DMs
    try:
        dms = colab.get_dms(20)
        unread = [dm for dm in dms if dm.get('to_claude') == 'Unity' and not dm.get('read_at')]
        # DMs to Unity from others (responses)
        responses = [dm for dm in dms if dm.get('to_claude') == 'Unity' and dm.get('from_claude') != 'Unity']
        results["channels"]["dms"] = True
        results["new_items"]["total_dms"] = len(dms)
        results["new_items"]["responses_to_unity"] = len(responses)
        if responses:
            # Get unique responders
            responders = list(set(dm.get('from_claude') for dm in responses))
            results["new_items"]["responders"] = responders
            results["needs_attention"].append(f"DM responses from: {', '.join(responders)}")
    except Exception as e:
        results["channels"]["dms"] = False
        results["needs_attention"].append(f"DMs channel error: {e}")

    # 5. CHECK WORK LOG (try to log, confirms channel works)
    try:
        log_result = colab.log_work('heartbeat', {'timestamp': results["timestamp"]})
        results["channels"]["work_log"] = log_result
    except Exception as e:
        results["channels"]["work_log"] = False
        results["needs_attention"].append(f"Work log channel error: {e}")

    # Update last heartbeat time
    _last_heartbeat = time.time()

    return results


def heartbeat_report() -> str:
    """Run heartbeat and return formatted report string"""
    results = heartbeat()

    if not results.get("connected"):
        return f"[HEARTBEAT FAILED] Not connected: {results.get('error', 'Unknown')}"

    lines = [
        "=" * 60,
        f"HEARTBEAT - {results['timestamp'][:19]}",
        "=" * 60,
        "",
        "CHANNEL STATUS:",
    ]

    for channel, status in results["channels"].items():
        icon = "[OK]" if status else "[FAIL]"
        lines.append(f"  {icon} {channel}")

    lines.append("")
    lines.append("COUNTS:")
    for key, val in results["new_items"].items():
        if isinstance(val, list):
            lines.append(f"  {key}: {', '.join(val)}")
        else:
            lines.append(f"  {key}: {val}")

    if results["needs_attention"]:
        lines.append("")
        lines.append("!! NEEDS ATTENTION:")
        for item in results["needs_attention"]:
            lines.append(f"  - {item}")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


def should_heartbeat() -> bool:
    """Check if enough time has passed for another heartbeat"""
    global _last_heartbeat
    if _last_heartbeat is None:
        return True
    return (time.time() - _last_heartbeat) >= _heartbeat_interval


def set_heartbeat_interval(seconds: int) -> None:
    """Set heartbeat interval in seconds (default 90)"""
    global _heartbeat_interval
    _heartbeat_interval = seconds


def get_new_dms() -> List[Dict]:
    """Get DMs sent TO Unity (responses from team)"""
    ensure_connected()
    dms = colab.get_dms(30)
    return [dm for dm in dms if dm.get('to_claude') == 'Unity' and dm.get('from_claude') != 'Unity']


def get_active_workers() -> List[str]:
    """Get list of workers who have claimed tasks"""
    ensure_connected()
    claimed = colab.get_tasks('claimed')
    return list(set(t.get('claimed_by') for t in claimed if t.get('claimed_by')))


def ping_all(message: str = "HEARTBEAT PING - Respond if active!") -> Dict[str, bool]:
    """Ping all known bots"""
    ensure_connected()
    bots = ['BLACK', 'INTOLERANT', 'OLLAMA', 'TheREV']
    results = {}
    for bot in bots:
        results[bot] = colab.send_dm(bot, message)
    return results


if __name__ == "__main__":
    print(heartbeat_report())
