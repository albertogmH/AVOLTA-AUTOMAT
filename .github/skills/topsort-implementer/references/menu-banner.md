# Contrato MENUBANNER

Tipo y carpeta: `MENUBANNER`. Banners de los desplegables del navbar de la home;
no son Trending ni un carrusel Swiper. Contrato de autoria, no prueba de SDK.

## Inventario Y Seleccion

Inspeccionar TODAS las entradas principales del navbar por home/store/idioma,
incluidas las que no tienen banners o no son elegibles para conversion. Nombre:
span del enlace principal o etiqueta del button. Categoria ID: sufijo numerico
de `.megamenu-wrapper[id="megamenu-wrapper-27"]`, corroborado con
`button[aria-controls="megamenu-wrapper-27"]`. No confundir con Store ID.
Registrar orden, nombre, Category ID, wrapper, region `.banner-blocks`, variantes
mobile/desktop, originales y tags Topsort por categoria. Entradas sin wrapper/ID
se reportan con dato desconocido, nunca se inventa una categoria.

Solo implementar estas tres familias con los IDs EXACTOS siguientes:

| Categoria | ID Topsort |
| --- | --- |
| Beauty | beauty-menu-banner-1 |
| Liquor | liquor-menu-banner-1 |
| Accessories | accesories-menu-banner-1 |

`accesories` es la grafia autorizada del ID, no corregirla. En otros idiomas,
identificar la familia por evidencia de navegacion/metadata de esa home, no por
posicion, numero global supuesto o traduccion inventada. Identidad incierta:
AMBIGUOUS, sin conversion. Otras entradas: reportar SIN_CAMBIOS_FUERA_DE_ALCANCE.

Inspeccionar ambas regiones `.banner-blocks.d-md-none` y
`.banner-blocks.d-none.d-md-flex` si existen. Un mirror de la misma fuente no
es otra campana ni otro banner original. No sumar copias mobile/desktop. Si
difieren y no se puede establecer la fuente original, bloquear esa categoria.
No modificar listas de enlaces, navbar, wrapper ni Page Builder de la pagina.

Tags Topsort reales dentro de la region de una categoria (incluido mirror):
SKIPPED_ALREADY_TOPSORT, aunque parcial, sin HTML nuevo ni reparacion implicita.
Continuar con las otras categorias. Solo declarar la home ya implementada si
TODAS sus categorias elegibles estan implementadas; no basta con una categoria.
En implementacion, una categoria elegible sin region tambien se crea con cero
fallbacks si el inventario es suficiente. En check solo, registrar ABSENT sin
generar. Fuente incompleta no equivale a cero banners.

## HTML De Autoria

Entregar un solo bloque por categoria, sin navbar ni wrapper `.banner-blocks`,
sin `<topsort-banner-mirror>`, location, language, estilos `--ts-banner-*` ni
comentarios/atributos de runtime. Forma autorizada del contenedor:

```html
<topsort-banner context width="600" height="400" id="beauty-menu-banner-1">
  <div class="menu-banners">
    <!-- Tres slots predefined, en orden HTML 1, 2, 3. -->
  </div>
</topsort-banner>
```

Cambiar solo el ID por el de la familia confirmada. Usar `context` sin valor;
no anadir `data-ts-no-context` del ejemplo anterior: el ultimo ejemplo de autoria
confirmado usa solo `context`. No copiar CSS de Trending ni anadir CSS inventado.

Cada slot contiene esta estructura de destinos dinamicos. Ejemplo vacio para un
slot sin fallback; no es una creatividad ni un motivo para marcar campos pendientes:

```html
<topsort-banner-slot predefined rank="1" data-ts-no-fallback>
  <div class="menu-banners__item">
    <a data-ts-field="target:href" class="menu-banners__itemImg -desktop">
      <img data-ts-field="mobileImage:src, altText: alt" class="only-mobile" alt="">
      <img data-ts-field="mainImage:src, altText: alt" class="only-desktop" alt="">
    </a>
    <div class="menu-banners__content">
      <p data-ts-field="headline:textContent" class="menu-banners__text"></p>
      <a data-ts-field="target:href, ctaText:textContent, ctaAriaLabel:aria-label"></a>
    </div>
  </div>
</topsort-banner-slot>
```

En slots con fallback, conservar imagenes mobile/desktop, srcset/sources si los
hay, alt, headline, CTA, aria-label y cada href autentico. Los href de imagen y
CTA pueden diferir: no igualarlos por compartir variable `target`. Si falta una
imagen/aria-label/texto, conservar destino dinamico sin inventar contenido ni
copiar otra campana. No usar `src=""`, `href="#"` ni placeholders como relleno.
Parsear mappings por pares separados por coma, tolerando espacios; variables y
propiedades case-sensitive. No aplicar los cuatro bindings de Trending.

## Ranks Y Fallbacks

Siempre EXACTAMENTE tres slots `predefined`, ranks unicos en orden DOM 1,2,3.
Con N originales visibles, conservar su orden relativo en los ultimos N ranks:

| Originales | Ranks con fallback | Ranks data-ts-no-fallback |
| --- | --- | --- |
| 0 | ninguno | 1,2,3 |
| 1 | 3 | 1,2 |
| 2 | 2,3 | 1 |
| 3 | 1,2,3 | ninguno |

Prioridad de permanencia 3, luego 2, luego 1; NO invertir el orden HTML ni el
orden de los originales. Slots nuevos sin fallback mantienen la estructura y
bindings vacios; no duplicar imagenes/copy de los visibles. `data-ts-no-fallback`
en el slot, no en el banner completo: no ocultar fallbacks reales por accidente.
El atributo permite ocultar cuando no hay respuesta/consentimiento, pero esa
conducta requiere SDK y no queda probada por inspeccion estatica.
Mas de tres originales: BLOCKED, pedir seleccion; no descartar silenciosamente.

El ejemplo de usuario incluye `{{block class="Magento\Cms\Block\Block"
block_id="menu_banner_additional"}}` y creatividades en slots nofallback.
Preservarlos solo si existen en la autoria suministrada, nunca agregarlos desde
el ejemplo ni inferir la directiva desde su DOM renderizado. Si el bloque opaco
impide saber el conteo/origen, pedir fuente; no duplicar su contenido expandido.

## Magento Y Fuentes

Autoria local: preservar directivas autenticas sin ejecutarlas. Captura live:
conservar URLs renderizadas completas, nunca inventar widgets/media/store.
Trabajar con copia desconectada; no modificar/publicar la web.

Dentro de `href="{{widget ...}}"`, Category Link debe usar exclusivamente
`template="Magento_Catalog::category/widget/link/link_href.phtml"`.
`link_block.phtml` y `link_inline.phtml` generan markup, no una URL; no entregarlos
en atributos. En conversion autorizada, corregir solo ese template manteniendo
id_path y demas datos, y registrar el ajuste. En categorias ya implementadas,
reportar defecto sin reparar salvo peticion expresa. Preservar literalmente las
comillas de la sintaxis Magento; un parser HTML generico puede no hacer round-trip.
Dialogo CMS: Template -> Category Link URL Only, no el Block preseleccionado.
Si se autoriza despues una comprobacion de pagina guardada: en view-source buscar
`href="<div`; deben ser cero coincidencias. No guardar/publicar para probarlo.

## Entrega Por Store E Idioma

Mantener fecha, grupo tipo/hostname, idiomas, confirmacion MD/chat y comparacion
conservadora del implementer. MENUBANNER sigue exactamente la estructura TRENDING:
`MENUBANNER-[host]/report.md` unico en la carpeta padre. Dentro del reporte, una
seccion por store/idioma con TODAS las categorias del navbar en orden y su
nombre/Category ID/estado. Cada categoria convertida incluye HTML completo y
enlace directo a su archivo en la subcarpeta de idioma. No MD por store/idioma
ni reportes dentro de carpetas de idiomas: estas contienen solo HTML.
No tablas de implementacion. Esta estructura rige tambien para futuros tipos
cuando tengan contrato soportado, no habilita tipos aun UNSUPPORTED.

HTML independiente por categoria para copiar solo su bloque:
`[idioma]/[CATEGORIA]-store-[IDs]-[idioma].html`. Prefijos exactos `BEAUTY`,
`LIQUOR` y `ACCESSORIES`; ejemplo `en/BEAUTY-store-196_198-en.html`.
Category ID permanece en el reporte y comentario, no en el filename. No cambiar
el ID Topsort `accesories-menu-banner-1` por usar `ACCESSORIES` en el filename.
Validar ausencia de colisiones; renombrado conserva bytes y actualiza enlaces,
sin regenerar contenido. Comentario con todos
los nombres/Store IDs/URLs, idioma y categoria/Category ID. No concatenar varias
categorias en un unico fragmento pegable. `report.md` del grupo contiene las
secciones de cada store/idioma y enlaza directamente los HTML; conservar resumen
raiz de omitidas/defectos. Una categoria
omitida se registra con su Store ID y Category ID aunque otras se conviertan.
Home totalmente implementada: indicarlo tambien en resumen general, sin HTML.

Solo compartir HTML entre stores si coinciden familia/Category ID, fallbacks,
campos (incluidos CTA/mobile), URLs completas, contexto y estructura de los tres
slots; conservar en el reporte padre todas las identidades de store/idioma
asociadas, con enlace y codigo comun completos.
No crear HTML para categorias ya implementadas o fuera de alcance. En chat usar
la misma estructura de home/idioma y categorias, sin crear archivos.

## Template Y Revision Propia

[CSV canonico](../assets/mega-menu-banner.csv): once columnas, siete campos;
required TRUE: headline, ctaText, mainImage, mobileImage, target; FALSE: altText,
ctaAriaLabel. Required define creatividad en Topsort, no contenido estatico.
CSV entregado no autoriza importacion. Documentacion de referencia del usuario:
https://www.npmjs.com/package/@topsort/banners (no instala ni cambia dependencias).

Check enfocado: inventario completo; decision por categoria; ID permitido y
unico; banner unico sin mirror/atributos cliente; ranks 1,2,3 y predefined;
tabla nofallback para N=0..3; estructura/bindings de siete campos; defaults,
orden y variantes conservados; widgets URL-only; MD/HTML/enlaces coherentes;
segunda conversion omite tags existentes sin doble wrapping. Mas de tres,
identidad ambigua o fuente incompleta bloquean solo el candidato afectado.
Revisar estaticamente 0/1/2/3 fallbacks, home mixta y home totalmente implementada;
no afirmar ejecucion CMS, consentimiento, subasta, mirror o SDK.