import re

# MITRE ATT&CK Mapping Heuristics
# A lightweight NLP/Heuristic engine to map shell commands to threat intent.

TACTICS = {
    "Credential Access": [
        r"cat\s+/etc/shadow",
        r"cat\s+/etc/passwd",
        r"grep.*password",
        r"hashcat",
        r"john"
    ],
    "Discovery": [
        r"whoami",
        r"id",
        r"uname",
        r"ifconfig",
        r"ip\s+a",
        r"netstat",
        r"ps\s",
        r"ls\s+-l"
    ],
    "Execution": [
        r"\./",
        r"sh\s+",
        r"bash\s+",
        r"chmod\s+\+x"
    ],
    "Command and Control": [
        r"wget\s+",
        r"curl\s+",
        r"nc\s+",
        r"netcat"
    ],
    "Defense Evasion": [
        r"rm\s+-rf",
        r"history\s+-c",
        r"export\s+HISTFILE="
    ]
}

def analyze_command(cmd):
    """
    Parses a shell command and returns the identified MITRE Tactic and severity.
    """
    cmd_lower = cmd.lower().strip()
    
    for tactic, patterns in TACTICS.items():
        for pattern in patterns:
            if re.search(pattern, cmd_lower):
                # Severity mapped: C2/Cred Access is High(3), Execution/Defense is Med(2), Discovery is Low(1)
                severity = 3 if tactic in ["Credential Access", "Command and Control"] else (2 if tactic in ["Execution", "Defense Evasion"] else 1)
                return {
                    "tactic": tactic,
                    "severity": severity,
                    "matched_pattern": pattern
                }
                
    return {
        "tactic": "Reconnaissance",
        "severity": 0,
        "matched_pattern": None
    }
