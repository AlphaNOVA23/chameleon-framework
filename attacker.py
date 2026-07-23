import paramiko
import sys
import threading
import time
import socket

try:
    import msvcrt
    WINDOWS = True
except ImportError:
    import tty
    import termios
    WINDOWS = False

def interactive_shell():
    print("=== CHAMELEON ATTACKER TERMINAL ===")
    print("Connecting to Cowrie Honeypot (127.0.0.1:2222)...")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Cowrie accepts any password
        client.connect('127.0.0.1', port=2222, username='root', password='password123')
        
        # CRITICAL: Disable Nagle's algorithm so Windows doesn't batch keystrokes
        # into bursts, which would ruin the biometric timing data!
        transport = client.get_transport()
        transport.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        
        print("Connected! You are now the attacker. Type 'exit' to quit.\n")
        
        channel = client.invoke_shell()
        
        def receive():
            while True:
                try:
                    if channel.recv_ready():
                        sys.stdout.write(channel.recv(1024).decode('utf-8', errors='ignore'))
                        sys.stdout.flush()
                    else:
                        time.sleep(0.01)
                except:
                    break

        threading.Thread(target=receive, daemon=True).start()
        
        # Send keystrokes instantly to preserve biometric IAT
        if WINDOWS:
            while True:
                if msvcrt.kbhit():
                    char = msvcrt.getch()
                    if char == b'\x03': # Ctrl+C
                        break
                    
                    # Convert Windows return (b'\r') to newline
                    if char == b'\r':
                        char = b'\n'
                        
                    channel.send(char)
                else:
                    time.sleep(0.01)
        else:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                while True:
                    char = sys.stdin.read(1)
                    if char == '\x03': # Ctrl+C
                        break
                    channel.send(char)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            
    except Exception as e:
        print(f"\nConnection failed: {e}")
        print("Make sure the Cowrie docker container is running!")
    finally:
        client.close()

if __name__ == "__main__":
    interactive_shell()
