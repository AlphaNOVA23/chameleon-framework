import os
import struct
from datetime import datetime

def parse_tty_chunk(data):
    """
    Parses a chunk of Cowrie binary TTY log.
    Format: 4 bytes sec, 4 bytes usec, 4 bytes len, 4 bytes dir, followed by string of len.
    Returns list of (timestamp_float, string_data).
    """
    results = []
    offset = 0
    while offset + 16 <= len(data):
        sec, usec, length, direction = struct.unpack_from('<iiii', data, offset)
        offset += 16
        
        if offset + length > len(data):
            break # Incomplete chunk
            
        chunk_data = data[offset:offset+length]
        offset += length
        
        if direction == 0: # INPUT (keystrokes from attacker)
            timestamp = sec + (usec / 1000000.0)
            try:
                text = chunk_data.decode('utf-8', errors='ignore')
                results.append((timestamp, text))
            except:
                pass
                
    return results, offset

def read_new_bytes(filepath, last_pos):
    """
    Opens, reads new bytes, and CLOSES the file immediately.
    This avoids holding a Windows file lock so Cowrie can rename the file!
    """
    try:
        with open(filepath, 'rb') as f:
            f.seek(last_pos)
            data = f.read()
            return data, f.tell()
    except Exception:
        return b"", last_pos
