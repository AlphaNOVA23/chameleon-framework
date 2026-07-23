import numpy as np

def calculate_metrics(timestamps):
    """
    Calculates key-by-key metrics (Gap 3).
    """
    if len(timestamps) < 2:
        return 0.0, 0.0, []
        
    iats = []
    for i in range(1, len(timestamps)):
        iat = timestamps[i] - timestamps[i-1]
        if iat < 5.0 and iat > 0: # Ignore massive pauses
            iats.append(iat)
            
    if not iats:
        return 0.0, 0.0, []
        
    mean_iat = float(np.mean(iats))
    var_iat = float(np.var(iats))
    return mean_iat, var_iat, iats

def classify(mean_iat, var_iat, num_keys):
    if num_keys < 5:
        return "UNKNOWN"
        
    # For the showcase, make thresholds very strict for bots/agents
    # so humans aren't accidentally flagged due to network jitter
    if mean_iat < 0.05 or (mean_iat < 0.1 and var_iat < 0.005):
        return "TIER_1_BOT"
    elif var_iat < 0.015:
        return "TIER_2_AGENT"
    else:
        return "TIER_3_HUMAN"
