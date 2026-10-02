import config_store

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
    if num_keys < 2:
        return "UNKNOWN"
        
    settings = config_store.load_settings()
    tau_bot = settings.get("tau_bot", 0.25)
    tau_human = settings.get("tau_human", 1.80)
    delta_var = settings.get("delta_var", 0.08)
    
    if mean_iat < tau_bot and var_iat < (delta_var / 4.0):
        return "TIER_1_BOT"
    elif mean_iat < tau_human:
        return "TIER_2_AGENT"
    else:
        return "TIER_3_HUMAN"

