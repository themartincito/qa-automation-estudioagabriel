# Análisis de causa raíz — estudioagabriel.com.ar

**Fecha:** 16/08/2026
**Sitio auditado:** https://www.estudioagabriel.com.ar (y alias https://estudioagabriel.ar)
**Herramientas:** Lighthouse CI, Lighthouse CLI, Playwright (Python), dnspython

## Resumen ejecutivo

El sitio presentaba dos problemas independientes:

1. **Crítico — Disponibilidad:** ambos dominios fallan al resolver DNS cuando el visitante usa un resolver público (Google 8.8.8.8, Cloudflare 1.1.1.1). Es un problema de infraestructura, no de código.
2. **Performance:** una sola imagen sin optimizar (`abogada.png`, 1.92 MB) representaba el 84% del peso total de la página, causando tiempos de carga lentos, especialmente en mobile/redes lentas.

El punto 2 se diagnosticó, se optimizó y el fix quedó preparado (ver sección "Fix aplicado"). El punto 1 requiere acción del proveedor de hosting/dominio.

---

## Hallazgo 1 (crítico): DNS SERVFAIL en resolvers públicos

**Evidencia:**

```
Resolve-DnsName estudioagabriel.com.ar -Server 8.8.8.8   -> sin respuesta (SERVFAIL)
Resolve-DnsName estudioagabriel.com.ar -Server 1.1.1.1   -> sin respuesta (SERVFAIL)
Resolve-DnsName estudioagabriel.com.ar (DNS del sistema) -> 162.241.60.39 (OK)

Resolve-DnsName estudioagabriel.ar -Server 8.8.8.8        -> sin respuesta (SERVFAIL)
```

**Causa:** los nameservers del dominio (`dns1/2/3.outergate.online`) no responden correctamente a resolvers públicos.

**Impacto:** cualquier visitante cuyo dispositivo o red use DNS público (Google DNS, Cloudflare DNS, DNS privado de Android, muchas VPNs corporativas y redes wifi de oficina) **no puede llegar al sitio en absoluto** — no es lentitud, es una falla total de resolución. Esto probablemente explica reportes de "el sitio no carga" que no están relacionados con el peso de la página.

**Automatizado como:** [`tests/test_dns_resolution.py`](../tests/test_dns_resolution.py) — corre como `xfail` (fallo esperado y trackeado) hasta que el proveedor de hosting corrija los nameservers. Cuando se corrija, el test pasa a XPASS automáticamente, señal de que se puede sacar el marcador de "known issue".

**Acción requerida:** contactar al proveedor de hosting/dominio para corregir la configuración de `dns1/2/3.outergate.online`. Esto está fuera del alcance de este proyecto de QA (no es algo que se arregle subiendo archivos al sitio).

---

## Hallazgo 2: imagen sin optimizar como cuello de botella principal

**Lighthouse — antes del fix (desktop, `estudioagabriel.com.ar`):**

| Métrica | Valor | Score |
|---|---|---|
| Performance | 74/100 | — |
| First Contentful Paint | 2.2s | bajo |
| Largest Contentful Paint | 2.5s | medio |
| Speed Index | 2.3s | medio |
| Peso total de página | 2,275 KB | — |

**En mobile (throttling 4G simulado) empeora notablemente:**

| Métrica | Desktop | Mobile |
|---|---|---|
| Performance | 74/100 | 71/100 |
| First Contentful Paint | 2.2s | 4.1s |
| Largest Contentful Paint | 2.5s | 5.2s |
| Speed Index | 2.3s | 4.4s |

*(Los mismos valores se repiten en el dominio `.ar`, confirmando que ambos alias sirven exactamente el mismo contenido.)*

**Causa raíz identificada:** el audit `modern-image-formats` y `uses-responsive-images` de Lighthouse apuntaron a un único recurso:

```
https://www.estudioagabriel.com.ar/abogada.png
  Tamaño real:      1920.1 KB  (1254×1254 px, PNG sin comprimir)
  Ahorro estimado:  1824.8 KB  si se sirve en formato moderno (WebP)
  Ahorro estimado:  1767.0 KB  si se sirve al tamaño real de renderizado
```

Esa sola imagen es el **84% del peso total de la página** (1920 KB de 2275 KB). El resto de la performance (tiempo de respuesta del servidor: 230ms, JavaScript, CSS) está bien — no son el problema.

**Automatizado como:** [`tests/test_performance.py::test_page_weight_budget`](../tests/test_performance.py) — falla si el peso total transferido supera 800 KB. Antes del fix, falla con ~2404 KB reportados. Sirve como test de regresión permanente.

---

## Fix aplicado

Se identificó que el código fuente real del sitio en producción es `preview/index.html` + `preview/abogada.png` (confirmado byte a byte contra el HTML e imagen servidos en vivo).

1. Se generó una versión optimizada de la imagen, redimensionada a 700×700px (tamaño de renderizado real en la sección "Sobre mí"):
   - `abogada.webp` — 32.5 KB (**98.3% más liviana**)
   - `abogada.jpg` — 60.6 KB (**96.9% más liviana**, fallback para navegadores sin soporte WebP)
2. Se actualizó `preview/index.html` para usar `<picture>` con WebP + fallback JPEG, más `loading="lazy"` y atributos `width`/`height` explícitos (evita layout shift).

**Pendiente (requiere acción manual del propietario del sitio):** subir `preview/abogada.webp`, `preview/abogada.jpg` y el `preview/index.html` actualizado al servidor vía FTP/cPanel, reemplazando los archivos actuales en el mismo directorio donde hoy vive `abogada.png`. No se realizó esta subida de forma automática por política de seguridad (no se usan credenciales de terceros para autenticarse en sistemas, ni siquiera con autorización explícita).

**Impacto esperado post-deploy:** peso de página baja de ~2275 KB a ~415 KB (imagen optimizada + resto de recursos sin cambios), el test `test_page_weight_budget` debería pasar, y LCP/Speed Index deberían mejorar sustancialmente, especialmente en mobile.

---

## Recomendaciones adicionales (no aplicadas, fuera de alcance de este ciclo)

- Corregir la codificación de caracteres del HTML (se detectaron artefactos tipo `Ã­`, `â€“` en el texto — indica mismatch de charset entre el archivo fuente y la declaración `<meta charset>`).
- Resolver el problema de DNS con el proveedor de hosting (Hallazgo 1).
- Rotar las credenciales de FTP, cPanel y la API key de Brevo utilizadas durante este diagnóstico, ya que se compartieron en texto plano en un canal de chat.
