"""
Test de infraestructura: valida que el dominio resuelva contra resolvers DNS
públicos (Google y Cloudflare), no solo contra el DNS por defecto del sistema.

Hallazgo (16/08/2026): los nameservers del dominio (dns1/2/3.outergate.online)
devolvían SERVFAIL en 8.8.8.8 y 1.1.1.1. El sitio SÍ resolvía con el DNS por
defecto de muchos ISPs, por eso el problema pasó desapercibido: una porción
de visitantes (los que usan DNS público, VPNs corporativas o Android con DNS
privado) directamente no podía llegar al sitio.

Resuelto (17/08/2026): se reemplazaron los nameservers en el registrador del
dominio (nic.ar). Este test corrió como xfail mientras el problema estuvo
abierto; al confirmarse el fix pasó a XPASS sin cambios de código, así que
se retiró el marcador y quedó como test normal de regresión.
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


@pytest.mark.parametrize("domain", DOMAINS)
@pytest.mark.parametrize("resolver_name,resolver_ip", PUBLIC_DNS_RESOLVERS.items())
def test_domain_resolves_via_public_dns(domain, resolver_name, resolver_ip):
    answer = resolve_via(domain, resolver_ip)
    assert len(answer) > 0, f"{domain} no resolvió via DNS de {resolver_name} ({resolver_ip})"
