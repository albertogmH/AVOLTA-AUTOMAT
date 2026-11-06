# Contrato What's Trending

Tipo de este contrato: `whats-trending` (`TRENDING`), contenido homepage.
MENUBANNER tiene contrato separado; no reutiliza este Swiper, campos ni CSS.
Contrato estatico suministrado por usuario, no especificacion de auction/SDK.

## Identidad Del Bloque

`.trending-brands` contiene header `h2`, a menudo `.heading-padding`, en
wrappers Page Builder row / column-group / column-line / column. Identificar
por titulo y estructura Swiper juntos, nunca por clase sola. Titulos literales:

- What's trending (comparacion de mayusculas/espacios sin alterar copy).
- Novedades (espanol).
- Que es tendencia (Cancun espanol; reconocer diacriticos en texto observado).
- Chino: decodificar `\u6d41\u884c\u8d8b\u52bf` / `\u6d41\u884c\u8da8\u52e2`
  como Unicode para comparar, no buscar estas secuencias literales en HTML.

`.trending-brands` tambien aparece en Most popular / Lo mas popular: excluir.
Guarulhos: Iconic brands & exclusive services / Marcas iconicas y servicios
exclusivos / Marcas iconicas e servicos exclusivos son posibles equivalentes
editoriales, no coincidencias literales. Requieren confirmacion explicita
usuario/editorial antes de clasificar como este tipo o transformar.
Titulos vacios o varios candidatos sin seleccion: AMBIGUOUS. Capturar titulo
real Unicode en evidencia; no sustituirlo por variantes normalizadas.

## DOM Y Fallback

Swiper seleccionado: `.swiper-container.py-0.brands-swiper1`, ID `brands-swiper`,
`.swiper-wrapper > .swiper-slide`, `.swiper-pagination`.
Texto: `.brand-text-area > .brand-name` (headline) y span (description).
Tarjeta original: anchor `d-flex align-items-center justify-content-center`;
img a menudo `loading="lazy" aria-hidden="true" alt="" width="270" height="318"`.
Estos atributos describen fuente habitual, no obligan a agregarlos: preservar
accesibilidad existente y no introducir aria-hidden para imagen significativa.

Preservar slides originales, orden/conteo, imagenes, links, copy y accesibilidad,
`{{store url='...'}}`, `{{media url=...}}`, CSS/JS/initializers, wrappers Page
Builder y campanas hidden desktop/mobile en fuente local. En captura live
autorizada, usar las URLs renderizadas sin reconstruir directivas Magento;
generar copia local del carrusel seleccionado y declarar alcance/limites.
No materializar ni ejecutar directivas existentes.
No tomar `transform:translate3d`, `transition-duration`, clases active ni clones
live como fuente. `.swiper-slide-duplicate` / `.slick-cloned` solo se excluyen
si son clones de runtime confirmados, no por parecido de contenido original.
Si hay duda, solicitar seleccion/fuente suficiente y no deduplicar campanas reales.
La captura live suficiente permite generar HTML sin export CMS. Normalizar la
envoltura documentada y anadir paginacion si falta, sin modificar la pagina live.
IDs canonicos deben ser unicos en autoria: distinguir duplicados runtime antes
de editar. Colision real requiere bloqueo/ajuste autorizado de initializer,
nunca renombrado silencioso ni nuevos IDs duplicados.

## Schema Estatico Topsort

- Un `<topsort-banner context width="600" height="400" id="whats-trending">`
  envuelve solo contenido Swiper seleccionado (incluida su paginacion), no h2,
  pagina completa u otras campanas. `context` es atributo presente sin valor.
- Dentro de cada slide ORIGINAL, un `<topsort-banner-slot predefined rank="1">`
  envuelve la tarjeta existente. `predefined` presente sin valor; ranks
  secuenciales unicos 1..N, no cinco obligatorios. Los cinco slides de la muestra
  del usuario son ejemplo, no limite ni conteo fijo.
- Bindings case-sensitive, una vez por elemento/campo en cada slot:

| Elemento existente | data-ts-field | Variable template |
| --- | --- | --- |
| Anchor tarjeta | target:href | target |
| Imagen tarjeta | mainImage:src | mainImage |
| .brand-name | headline:textContent | headline |
| Span descripcion | description:textContent | description |

Los bindings son destinos de contenido dinamico de Topsort. Un elemento como
`<span data-ts-field="description:textContent"></span>` es valido aunque este
vacio: no marcar descripcion pendiente, HTML parcial o BLOCKED por eso. Validar
que el nodo, la variable y la propiedad existan, no que haya texto estatico.
`required TRUE` del CSV define campos del template creativo en Topsort, no exige
defaults no vacios en el HTML CMS. Conservar defaults de fuente si existen;
Topsort rellena la variable; no confundir texto vacio con ausencia del atributo
`data-ts-field="description:textContent"`. Solo si falta ese atributo en el
slot se informa un binding ausente, indicando el atributo exacto, no contenido
pendiente. No inventar copy ni reemplazar imagenes/links por el ejemplo Prada. Tags fuera
del bloque, en scripts o clases no cuentan. Validez exige estructura, atributos,
mappings presentes y sin nesting/slots/bindings duplicados; no prueba
runtime. Implementacion de lote: tags reales presentes, TOPSORT_PARTIAL o
TOPSORT_VALID, implica SKIPPED_ALREADY_TOPSORT, sin HTML nuevo y con aviso.
Repair solo ante peticion explicita, no automaticamente por pedir implementar.

## Ejemplo Compacto De Estructura

Los valores EXISTING_* son simbolos de defaults autenticos de fuente, no
contenido que se deba inventar o pegar. Una slide ilustra N; conservar todas
las originales y wrappers/orden reales. No usar el ejemplo para reconstruir
markup que no coincide con fuente.

```html
<div class="trending-brands">
  <h2 class="heading-padding">What's trending</h2>
  <topsort-banner context width="600" height="400" id="whats-trending">
    <div class="swiper-container py-0 brands-swiper1" id="brands-swiper">
      <div class="swiper-wrapper">
        <div class="swiper-slide">
          <topsort-banner-slot predefined rank="1">
            <a class="d-flex align-items-center justify-content-center" href="{{store url='EXISTING_TARGET'}}" data-ts-field="target:href">
              <img loading="lazy" width="270" height="318" src="{{media url='EXISTING_IMAGE'}}" alt="EXISTING_ALT" data-ts-field="mainImage:src">
              <div class="brand-text-area">
                <div class="brand-name" data-ts-field="headline:textContent">EXISTING_HEADLINE</div>
                <span data-ts-field="description:textContent">EXISTING_DESCRIPTION</span>
              </div>
            </a>
          </topsort-banner-slot>
        </div>
      </div>
      <div class="swiper-pagination"></div>
    </div>
  </topsort-banner>
</div>
```

## CSS Documentado Al Final

El usuario autoriza este CSS, incluidas las reglas de `body, html`. Incluirlo al
final de cada fragmento generado, despues de `</topsort-banner>`, y en su copia
del MD/chat. Un unico bloque con estas reglas; no duplicarlo si ya esta completo.
Preservar otros estilos y cambios del usuario; conflictos requieren revision,
no sobrescritura silenciosa. No publicar ni cambiar CSS de la pagina live.

```html
<style>
  .trending-brands .row-full-width-inner {
    max-width: unset !important;
  }
  .trending-brands > .pagebuilder-column-group {
    width: 100%;
  }
  .trending-brands .swiper-container {
    overflow: visible;
  }
  body,
  html {
    overflow-x: hidden;
  }
  @media only screen and (max-width: 768px) {
    .trending-brands #brands-swiper {
      margin-top: 20px;
      padding: 0 20px;
    }
  }
</style>
```

## Template CSV

[Asset canonico](./../assets/trending-banner-carousel.csv), confirmado con parser
contra original del usuario. Es TEMPLATE DEFINITION para importacion en plataforma
Topsort, no inventario de tarjetas, HTML upload ni creative bulk import.
Header exacto de once columnas; cuatro filas de campos required `TRUE`, variables
case-sensitive `mainImage`, `target`, `headline`, `description`. Preservar valores,
vacios y descripcion de formatos/30 MB. No implica permiso de importacion/API.

## Evidencia Y Limites

Checker informa ABSENT, PRESENT_NO_TOPSORT, TOPSORT_PARTIAL, TOPSORT_VALID,
AMBIGUOUS o ERROR/BLOCKED por candidato, con fuente/final URL, host + store
code/id, idioma, timestamp/viewport medido, tags/attrs, campos/ranks y variantes.
Sin navegador/fuente suficiente: no verificado, nunca ausencia asumida.
Fuente puede ser autoria local o `live-dom` autorizado; declarar cual se uso.
Salida para usuario: seccion `NOMBRE ID:<store_id> - <URL completa>` y codigo
completo en bloque fenced `html`, tanto por chat como MD, no tabla de implementacion.
Reportes minimos: estado esencial, enlace y codigo; sin boilerplate de fuente,
viewport, formato/ruta ni checks. Advertencias estructurales reales permanecen
breves; descripcion dinamica vacia no es pendiente. MD agrupa por fecha `dd-mm-yy-hhmm` y por
`TIPO-store`, con resumen raiz de ya implementadas, ausentes y fallidas.
Comparacion local antes/despues y segunda ejecucion NO_OP preceden pruebas
runtime autorizadas desktop/mobile. Las pruebas de instrucciones/ejemplo no
son enforcement runtime ni prueba de auction/SDK. Evidencia historica de reports
2026-11-05 no certifica resultados live permanentes.