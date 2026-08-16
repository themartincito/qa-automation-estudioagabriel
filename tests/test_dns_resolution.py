"""
Test de infraestructura: valida que el dominio resuelva contra resolvers DNS
públicos (Google y Cloudflare), no solo contra el DNS por defecto del sistema.

Hallazgo (16/08/2026): los nameservers del dominio (dns1/2/3.outergate.online)
devuelven SERVFAIL en 8.8.8.8 y 1.1.1.1. El sitio SÍ resuelve con el DNS por
defecto de muchos ISPs, por eso el problema pasó desapercibido: una porción
de visitantes (los que usan DNS público, VPNs corporativas o Android con DNS
privado) directamente no puede llegar al sitio.

Se marca xfail (fallo esperado y trackeado) en lugar de fallar en rojo sin
contexto: es un problema de infraestructura DNS a resolver por el proveedor
de hosting/dominio, no por cambios en el código del sitio. Cuando el
proveedor lo resuelva, este test va a pasar solo y pytest lo va a reportar
como XPASS, señal de que se puede sacar el marker.
"""
import dns.resolver
import pytest
from conftest import DOMAINS, PUBLIC_DNS_RESOLVERS


def resolve_via(domain: str, resolver_ip: str):
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = [resolver_ip]
    resolver.lifetime = 8
    hostname = domain.replace("https://", "").replace("http://", "").rstrip("/")
    return resolver.resolve(hostname, "A")


@pytest.mark.xfail(
    reason="DNS SERVFAIL conocido en dns1/2/3.outergate.online para resolvers publicos (ver docstring)",
    strict=False,
)
@pytest.mark.parametrize("domain", DOMAINS)
@pytest.mark.parametrize("resolver_name,resolver_ip", PUBLIC_DNS_RESOLVERS.items())
def test_domain_resolves_via_public_dns(domain, resolver_name, resolver_ip):
    answer = resolve_via(domain, resolver_ip)
    assert len(answer) > 0, f"{domain} no resolvió via DNS de {resolver_name} ({resolver_ip})"
