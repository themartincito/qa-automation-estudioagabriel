"""Chequeos básicos de disponibilidad para ambos dominios del sitio."""
import pytest
from conftest import DOMAINS


@pytest.mark.parametrize("domain", DOMAINS)
def test_domain_returns_200(page, domain):
    response = page.goto(domain, wait_until="load", timeout=30000)
    assert response is not None, f"No hubo respuesta de {domain}"
    assert response.status == 200, f"{domain} respondió con status {response.status}"


@pytest.mark.parametrize("domain", DOMAINS)
def test_http_redirects_to_https(page, domain):
    http_url = domain.replace("https://", "http://")
    response = page.goto(http_url, wait_until="load", timeout=30000)
    assert page.url.startswith("https://"), (
        f"{http_url} no redirigió a HTTPS (terminó en {page.url})"
    )


@pytest.mark.parametrize("domain", DOMAINS)
def test_page_has_expected_title(page, domain):
    page.goto(domain, wait_until="load", timeout=30000)
    assert "Gabriel" in page.title(), f"Título inesperado en {domain}: {page.title()}"
