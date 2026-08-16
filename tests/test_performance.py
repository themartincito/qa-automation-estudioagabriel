"""
Tests de performance: presupuesto de peso de página y tiempos de carga
bajo distintas condiciones de red simuladas (CDP Network.emulateNetworkConditions).
"""
import time

import pytest
from conftest import DOMAINS, NETWORK_PROFILES, PAGE_WEIGHT_BUDGET_KB


@pytest.mark.parametrize("domain", DOMAINS)
def test_page_weight_budget(page, domain):
    """El peso total transferido no debería superar el presupuesto definido.

    Antes del fix (imagen abogada.png de 1.9MB sin optimizar) este test
    fallaba con ~2275 KB transferidos. Sirve como regresión: si alguien
    vuelve a subir una imagen pesada sin optimizar, el test lo detecta.
    """
    total_bytes = 0

    def on_response(response):
        nonlocal total_bytes
        try:
            body = response.body()
            total_bytes += len(body)
        except Exception:
            pass  # recursos redirigidos / sin body accesible, se ignoran

    page.on("response", on_response)
    page.goto(domain, wait_until="networkidle", timeout=30000)

    total_kb = total_bytes / 1024
    assert total_kb <= PAGE_WEIGHT_BUDGET_KB, (
        f"{domain} transfirió {total_kb:.0f} KB, supera el presupuesto de "
        f"{PAGE_WEIGHT_BUDGET_KB} KB"
    )


@pytest.mark.parametrize("domain", DOMAINS)
@pytest.mark.parametrize("profile_name", NETWORK_PROFILES.keys())
def test_load_time_under_network_conditions(page, domain, profile_name):
    """Mide el tiempo de carga real bajo condiciones de red simuladas.

    Útil para saber cómo se comporta el sitio para usuarios con mala señal
    (3G) vs conexión hogareña normal (4G) vs sin throttling.
    """
    cdp = page.context.new_cdp_session(page)
    cdp.send("Network.enable")
    cdp.send("Network.emulateNetworkConditions", NETWORK_PROFILES[profile_name])

    start = time.monotonic()
    page.goto(domain, wait_until="load", timeout=60000)
    elapsed = time.monotonic() - start

    print(f"\n[{profile_name}] {domain} cargó en {elapsed:.2f}s")

    # Bajo throttling agresivo (3G) toleramos más tiempo; sin throttling, exigimos más.
    threshold = {"sin_throttling": 5, "4g_regular": 8, "3g_rapido": 15}[profile_name]
    assert elapsed <= threshold, (
        f"{domain} tardó {elapsed:.2f}s en cargar con perfil '{profile_name}' "
        f"(umbral: {threshold}s)"
    )
