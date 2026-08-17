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

## Fix aplicado y verificado en producción (17/08/2026)

Se identificó que el código fuente real del sitio en producción es `preview/index.html` + `preview/abogada.png` (confirmado byte a byte contra el HTML e imagen servidos en vivo).

1. Se generó una versión optimizada de la imagen, redimensionada a 700×700px (tamaño de renderizado real en la sección "Sobre mí"):
   - `abogada.webp` — 32.5 KB (**98.3% más liviana**)
   - `abogada.jpg` — 60.6 KB (**96.9% más liviana**, fallback para navegadores sin soporte WebP)
2. Se actualizó `preview/index.html` para usar `<picture>` con WebP + fallback JPEG, más `loading="lazy"` y atributos `width`/`height` explícitos (evita layout shift).
3. Se subieron los 3 archivos al servidor vía cPanel File Manager (acción manual del propietario del sitio, confirmada por captura de pantalla) y se verificó en vivo que `abogada.webp` y `abogada.jpg` responden 200 OK y que el HTML servido ya referencia la versión optimizada.

### Resultado medido (Lighthouse, antes vs. después del deploy)

| Métrica | Antes | Después | Cambio |
|---|---|---|---|
| Peso total de página (desktop) | 2,275 KB | **387 KB** | **−83%** |
| Peso total de página (mobile) | 2,275 KB | **354 KB** | **−84%** |
| Performance score (desktop) | 74/100 | 74/100 | sin cambio |
| Performance score (mobile) | 71/100 | 70/100 | sin cambio |
| First Contentful Paint (desktop) | 2.2s | 2.2s | sin cambio |
| Largest Contentful Paint (desktop) | 2.5s | 2.5s | sin cambio |
| Speed Index (desktop) | 2.3s | 2.3s | sin cambio |

**Test de regresión (`test_page_weight_budget`):** pasó de `FAILED` (2404 KB, presupuesto 800 KB) a `PASSED` en ambos dominios. Evidencia objetiva de que el fix se aplicó correctamente.

### Por qué el LCP no mejoró (hallazgo honesto, no esperado)

El peso de página bajó drásticamente, pero el **Largest Contentful Paint no se movió**. Investigando el motivo: el elemento LCP real del sitio **nunca fue la imagen `abogada.png`** — es el `<h1>` del hero ("Concursos y Quiebras"), ubicado muy arriba en la página. La imagen pesada estaba en la sección "Sobre mí", mucho más abajo, fuera del viewport inicial. Por eso el fix reduce drásticamente el ancho de banda transferido (importante para mobile/datos móviles) pero no mueve la métrica de percepción de velocidad de carga inicial.

## Hallazgo 3: render-blocking de Google Fonts retrasa el LCP real

Con el audit `render-blocking-resources` del reporte "después" se identificó la causa real del retraso en el `<h1>`:

```
Render-blocking: https://fonts.googleapis.com/css2?family=Cormorant+Garamond...&family=Montserrat...
```

El navegador no puede pintar el texto del `<h1>` hasta:
1. Descargar el CSS de Google Fonts (`fonts.googleapis.com`)
2. Ese CSS le indica descargar los archivos de fuente reales (`fonts.gstatic.com`, formato `.woff2`)

Son 2 round-trips a dominios de terceros antes de poder mostrar el título principal — esto explica el FCP/LCP de ~2.2-2.5s pese a que el servidor responde en 230ms.

**No se aplicó fix para este hallazgo en este ciclo** (requiere decidir estrategia: `font-display: swap`, `<link rel="preconnect">` a los dominios de Google Fonts, o self-hosting de las fuentes). Queda documentado como próximo paso.

---

## Recomendaciones adicionales (no aplicadas, fuera de alcance de este ciclo)

- Corregir la codificación de caracteres del HTML (se detectaron artefactos tipo `Ã­`, `â€“` en el texto — indica mismatch de charset entre el archivo fuente y la declaración `<meta charset>`).
- Resolver el problema de DNS con el proveedor de hosting (Hallazgo 1).
- Rotar las credenciales de FTP, cPanel y la API key de Brevo utilizadas durante este diagnóstico, ya que se compartieron en texto plano en un canal de chat.
