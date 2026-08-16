"""Configuración compartida para los tests de QA de estudioagabriel.com.ar"""

DOMAINS = [
    "https://www.estudioagabriel.com.ar",
    "https://estudioagabriel.ar",
]

# Perfiles de red simulados vía Chrome DevTools Protocol (Network.emulateNetworkConditions).
# Valores estándar usados por Chrome DevTools / Lighthouse.
NETWORK_PROFILES = {
    "sin_throttling": {"offline": False, "latency": 0, "downloadThroughput": -1, "uploadThroughput": -1},
    "4g_regular": {"offline": False, "latency": 170, "downloadThroughput": 4 * 1024 * 1024 / 8, "uploadThroughput": 3 * 1024 * 1024 / 8},
    "3g_rapido": {"offline": False, "latency": 562, "downloadThroughput": 1.6 * 1024 * 1024 / 8, "uploadThroughput": 750 * 1024 / 8},
}

# Presupuesto de peso de página recomendado para un sitio de landing institucional (KB).
PAGE_WEIGHT_BUDGET_KB = 800

PUBLIC_DNS_RESOLVERS = {
    "Google": "8.8.8.8",
    "Cloudflare": "1.1.1.1",
}
