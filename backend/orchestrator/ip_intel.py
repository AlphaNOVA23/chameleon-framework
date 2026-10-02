import random
import ipaddress

# Simulated Geolocation & Threat Intelligence DB for local demo & offline reliability
IP_GEOLOCATION_DB = {
    "192.168": {"country": "Internal Subnet", "code": "US", "flag": "🇺🇸", "isp": "Corporate LAN", "risk": "Low", "threat_score": 5},
    "10.0": {"country": "Private Network", "code": "US", "flag": "🇺🇸", "isp": "Intranet DMZ", "risk": "Low", "threat_score": 10},
    "127.0": {"country": "Localhost", "code": "US", "flag": "🇺🇸", "isp": "Loopback", "risk": "Low", "threat_score": 0},
    "45.": {"country": "Russia", "code": "RU", "flag": "🇷🇺", "isp": "AS14061 DigitalOcean LLC", "risk": "High Risk", "threat_score": 92},
    "185.": {"country": "Germany", "code": "DE", "flag": "🇩🇪", "isp": "AS24940 Hetzner Online GmbH", "risk": "Moderate", "threat_score": 68},
    "103.": {"country": "China", "code": "CN", "flag": "🇨🇳", "isp": "AS4134 CHINANET-BACKBONE", "risk": "High Risk", "threat_score": 96},
    "198.": {"country": "United States", "code": "US", "flag": "🇺🇸", "isp": "AS16509 Amazon.com Inc.", "risk": "Low", "threat_score": 25},
    "141.": {"country": "Netherlands", "code": "NL", "flag": "🇳🇱", "isp": "AS16276 OVH SAS", "risk": "High Risk (Tor Exit)", "threat_score": 88}
}

DEFAULT_PROVIDERS = [
    {"country": "United States", "code": "US", "flag": "🇺🇸", "isp": "AS16509 Amazon Web Services"},
    {"country": "Germany", "code": "DE", "flag": "🇩🇪", "isp": "AS24940 Hetzner Online"},
    {"country": "Netherlands", "code": "NL", "flag": "🇳🇱", "isp": "AS16276 OVH Cloud"},
    {"country": "United Kingdom", "code": "GB", "flag": "🇬🇧", "isp": "AS5607 British Telecom"},
    {"country": "Singapore", "code": "SG", "flag": "🇸🇬", "isp": "AS45102 Alibaba Cloud"}
]

def enrich_ip(ip_address: str) -> dict:
    """
    Enriches an attacker IP address with Country Flag, ISP / ASN, Location,
    and Threat Risk Score.
    """
    if not ip_address or ip_address == "?":
        return {
            "country": "Unknown Origin",
            "code": "UN",
            "flag": "🌐",
            "isp": "Unresolved ISP",
            "risk": "Moderate",
            "threat_score": 50
        }
        
    for prefix, data in IP_GEOLOCATION_DB.items():
        if ip_address.startswith(prefix):
            return {
                "country": data["country"],
                "code": data["code"],
                "flag": data["flag"],
                "isp": data["isp"],
                "risk": data["risk"],
                "threat_score": data["threat_score"]
            }
            
    # Deterministic hash fallback for unknown IP ranges
    seed_num = sum(ord(c) for c in ip_address)
    provider = DEFAULT_PROVIDERS[seed_num % len(DEFAULT_PROVIDERS)]
    score = (seed_num * 17) % 80 + 15
    risk = "High Risk" if score > 75 else "Moderate" if score > 40 else "Low"
    
    return {
        "country": provider["country"],
        "code": provider["code"],
        "flag": provider["flag"],
        "isp": provider["isp"],
        "risk": risk,
        "threat_score": score
    }
