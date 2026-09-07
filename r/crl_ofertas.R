# Funciones para bajar y puntuar ofertas de café en Mercado Público (CRL Coffee).
# Dependencias: httr, jsonlite. En RStudio: install.packages(c("httr", "jsonlite"))

LICITACIONES_URL <- "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"
COMPRA_AGIL_URL <- "https://api2.mercadopublico.cl/v2/compra-agil"
PORTAL_LICITACION <- paste0(
  "https://www.mercadopublico.cl/Procurement/Modules/RFB/",
  "DetailsAcquisition.aspx?idlicitacion="
)
PORTAL_COMPRA_AGIL <- "https://www.mercadopublico.cl/Home/Search?k="

BUSQUEDAS_COMPRA_AGIL <- c("café", "cafe", "coffe", "cafetería", "cafeteria", "nescafe")
UNSPSC_CAFE_GRANO <- c("50201706")
UNSPSC_CAFE_INSTANTANEO <- c("50201709", "50201708")
UNSPSC_EQUIPO_CAFE <- c("52141526", "52141529", "48101513", "48101514")
UNSPSC_SERVICIO_CAFE <- c("90101603", "90101701", "90111603", "90101500")

RE_CONCESION <- "(^|\\s)concesion(es)?(\\s|$)|arriendo de (espacio|local)"
RE_OBRA <- "(^|\\s)(construccion|arquitectura|especialidades tecnicas|obra publica)(\\s|$)"
RE_REPARACION <- "reparacion(es)?.*\\b(maquina|cafetera|equipo)"
RE_ESPECIALIDAD_MEDICA <- "(^|\\s)(medico|medica|cirugia|traumatolog|enfermer|clinico|dental|salud)(\\s|$)"
RE_CAFE <- "(^|\\s)(cafe|coffee|coffe|cafeteria|cafetera|espresso|barista|arabica)(\\s|$)"
RE_GRANO <- "(^|\\s)(granos?|en grano|grano entero|grano arabica|grano selecto|cafe de especialidad)(\\s|$)"
RE_TOSTADO <- "(^|\\s)(tostad[oa]s?|tueste|torrefacci)"
RE_ORIGEN <- "(^|\\s)(especialidad|origen|colombia|brasil|etiopia|guatemala|peru|honduras|rwanda|geisha|arabica|catuai|caturra)(\\s|$)"
RE_INSTANTANEO <- "(^|\\s)(nescafe|liofilizad[oa]|instantane[oa]|soluble|tarros? de cafe|cafe en tarro)(\\s|$)"
RE_SERVICIO <- "(^|\\s)(coffe(e)? break|coffee break|servicio de (cafe|cafeteria|catering)|catering|brunch)(\\s|$)"
RE_INSUMOS <- "insumos (de )?(cafeteria|cafe)|compra de cafe|adquisicion de cafe"
RE_MAQUINA <- "(^|\\s)(maquina|dispensadora|comodato|cafetera|molinillo|moledor)(\\s|$)"

`%||%` <- function(a, b) {
  if (is.null(a) || length(a) == 0 || (length(a) == 1 && is.na(a))) b else a
}

as_chr <- function(x, default = "") {
  if (is.null(x) || length(x) == 0) {
    return(default)
  }
  val <- unlist(x, use.names = FALSE)[1]
  if (is.null(val) || is.na(val)) default else as.character(val)
}

as_num <- function(x) {
  if (is.null(x) || length(x) == 0) {
    return(NA_real_)
  }
  val <- suppressWarnings(as.numeric(unlist(x, use.names = FALSE)[1]))
  if (length(val) == 0) NA_real_ else val
}

pluck_chr <- function(x, ...) {
  for (key in list(...)) {
    if (is.null(x)) {
      return("")
    }
    x <- x[[key]]
  }
  as_chr(x, "")
}

pluck_num <- function(x, ...) {
  for (key in list(...)) {
    if (is.null(x)) {
      return(NA_real_)
    }
    x <- x[[key]]
  }
  as_num(x)
}

fold <- function(text) {
  value <- as_chr(text, "")
  value <- iconv(value, from = "UTF-8", to = "ASCII//TRANSLIT", sub = "")
  if (is.na(value)) {
    value <- as_chr(text, "")
  }
  value <- tolower(value)
  value <- gsub("[^a-z0-9[:space:]]", " ", value, perl = TRUE)
  value <- gsub("[[:space:]]+", " ", value, perl = TRUE)
  trimws(value)
}

re_hay <- function(patron, texto) {
  grepl(patron, texto, perl = TRUE, ignore.case = TRUE)
}

ticket_mp <- function(ticket = NULL) {
  valor <- ticket %||% Sys.getenv("MERCADO_PUBLICO_TICKET", unset = "")
  if (!nzchar(valor)) {
    valor <- Sys.getenv("CHILE_PUBLIC_MARKET_TICKET", unset = "")
  }
  valor <- trimws(valor)
  if (!nzchar(valor) || identical(valor, "TU_TICKET_AQUI")) {
    stop(
      "Falta el ticket de Mercado Público.\n",
      "Pídelo con Clave Única en https://www.chilecompra.cl/api/\n",
      "y defínelo con Sys.setenv(MERCADO_PUBLICO_TICKET = '...')",
      call. = FALSE
    )
  }
  valor
}

.get_json <- function(url, query = list(), headers = list(), timeout_sec = 22, reintentos = 3) {
  ua <- httr::user_agent("crl-coffee-ofertas-r/1.0")
  extra <- do.call(httr::add_headers, headers)
  last_error <- NULL
  for (intento in seq_len(reintentos)) {
    resp <- tryCatch(
      httr::GET(url, query = query, extra, ua, httr::timeout(timeout_sec)),
      error = function(e) e
    )
    if (inherits(resp, "error")) {
      last_error <- resp
      Sys.sleep(min(8, 2^intento))
      next
    }
    status <- httr::status_code(resp)
    texto <- httr::content(resp, as = "text", encoding = "UTF-8")
    if (status %in% c(429, 500, 502, 503) && intento < reintentos) {
      Sys.sleep(min(12, 2^intento))
      next
    }
    if (status >= 400) {
      stop(sprintf("HTTP %s en %s: %s", status, url, substr(texto, 1, 300)), call. = FALSE)
    }
    if (!nzchar(texto)) {
      return(NULL)
    }
    return(jsonlite::fromJSON(texto, simplifyVector = FALSE))
  }
  stop(sprintf("Sin respuesta de %s: %s", url, last_error$message %||% last_error), call. = FALSE)
}

compras_agiles <- function(ticket, query, estado = "publicada", page_size = 50, max_pages = 4) {
  items <- list()
  for (page in seq_len(max_pages)) {
    data <- .get_json(
      COMPRA_AGIL_URL,
      query = list(
        q = query,
        estado = estado,
        tamano_pagina = page_size,
        numero_pagina = page,
        ordenar_por = "FechaPublicacion"
      ),
      headers = list(ticket = ticket)
    )
    if (is.null(data) || !identical(data$success, "OK")) {
      stop(sprintf("Compra Ágil rechazó q='%s'", query), call. = FALSE)
    }
    batch <- data$payload$items %||% list()
    items <- c(items, batch)
    total_pages <- as.integer(data$payload$paginacion$total_paginas %||% 1)
    if (page >= total_pages || length(batch) == 0) {
      break
    }
    Sys.sleep(0.35)
  }
  items
}

compra_agil_detalle <- function(ticket, codigo) {
  data <- .get_json(
    paste0(COMPRA_AGIL_URL, "/", codigo),
    headers = list(ticket = ticket)
  )
  if (is.null(data) || !identical(data$success, "OK")) {
    return(NULL)
  }
  data$payload
}

licitaciones_activas <- function(ticket) {
  data <- .get_json(LICITACIONES_URL, query = list(estado = "activas", ticket = ticket))
  data$Listado %||% list()
}

licitacion_detalle <- function(ticket, codigo) {
  data <- .get_json(LICITACIONES_URL, query = list(codigo = codigo, ticket = ticket))
  listado <- data$Listado %||% list()
  if (length(listado) == 0) NULL else listado[[1]]
}

parece_cafe <- function(texto) {
  n <- fold(texto)
  if (!re_hay(RE_CAFE, n)) {
    return(FALSE)
  }
  if (re_hay(RE_ESPECIALIDAD_MEDICA, n) && !grepl("cafe", n, fixed = TRUE) && !grepl("coffee", n, fixed = TRUE)) {
    return(FALSE)
  }
  if (re_hay(RE_OBRA, n) && !re_hay(RE_INSUMOS, n)) {
    return(FALSE)
  }
  TRUE
}

productos_desde_compra_agil <- function(data) {
  crudos <- data$productos_solicitados %||% list()
  lapply(crudos, function(prod) {
    list(
      codigo = as_chr(prod$codigo_producto),
      nombre = as_chr(prod$nombre),
      descripcion = as_chr(prod$descripcion),
      cantidad = as_num(prod$cantidad),
      unidad = as_chr(prod$unidad_medida)
    )
  })
}

productos_desde_licitacion <- function(data) {
  crudos <- data$Items$Listado %||% list()
  lapply(crudos, function(item) {
    list(
      codigo = as_chr(item$CodigoProducto),
      nombre = as_chr(item$NombreProducto),
      descripcion = as_chr(item$Descripcion),
      cantidad = as_num(item$Cantidad),
      unidad = as_chr(item$UnidadMedida)
    )
  })
}

corpus_oferta <- function(oferta) {
  partes <- c(oferta$nombre, oferta$descripcion)
  for (prod in oferta$productos) {
    partes <- c(partes, prod$nombre, prod$descripcion, prod$codigo)
  }
  fold(paste(partes[nzchar(partes)], collapse = " "))
}

categoria_de <- function(puntaje, texto, encaja_producto) {
  if (re_hay(RE_CONCESION, texto) && !re_hay(RE_INSUMOS, texto)) {
    return("descartada")
  }
  if (puntaje < 18) {
    return("descartada")
  }
  if (isTRUE(encaja_producto) && puntaje >= 70) {
    return("excelente")
  }
  if (isTRUE(encaja_producto) && puntaje >= 45) {
    return("buena")
  }
  if (re_hay(RE_INSTANTANEO, texto)) {
    return("regular")
  }
  if (re_hay(RE_SERVICIO, texto) && !isTRUE(encaja_producto)) {
    return("servicio")
  }
  if (puntaje >= 45) {
    return("buena")
  }
  "regular"
}

puntuar <- function(oferta) {
  texto <- corpus_oferta(oferta)
  unspsc <- unique(vapply(oferta$productos, function(p) as_chr(p$codigo), character(1)))
  razones <- character()
  score <- 0
  encaja <- FALSE

  if (!re_hay(RE_CAFE, texto) && !any(unspsc %in% c(UNSPSC_CAFE_GRANO, UNSPSC_CAFE_INSTANTANEO))) {
    oferta$puntaje <- 0
    oferta$categoria <- "descartada"
    oferta$razones <- "No menciona café ni códigos UNSPSC de café"
    oferta$encaja_producto <- FALSE
    return(oferta)
  }
  if (re_hay(RE_CONCESION, texto) && !re_hay(RE_INSUMOS, texto)) {
    oferta$puntaje <- 5
    oferta$categoria <- "descartada"
    oferta$razones <- "Es concesión o arriendo de cafetería, no suministro de café"
    oferta$encaja_producto <- FALSE
    return(oferta)
  }
  if (re_hay(RE_REPARACION, texto) && !re_hay(RE_GRANO, texto) && !any(unspsc %in% UNSPSC_CAFE_GRANO)) {
    oferta$puntaje <- 8
    oferta$categoria <- "descartada"
    oferta$razones <- "Es reparación de máquina, no venta de café"
    oferta$encaja_producto <- FALSE
    return(oferta)
  }

  if (any(unspsc %in% UNSPSC_CAFE_GRANO)) {
    score <- score + 40
    encaja <- TRUE
    razones <- c(razones, "Ítem UNSPSC 50201706 (Café)")
  }
  if (re_hay(RE_GRANO, texto)) {
    score <- score + 35
    encaja <- TRUE
    razones <- c(razones, "Pide café en grano o de especialidad")
  }
  if (re_hay(RE_TOSTADO, texto)) {
    score <- score + 15
    encaja <- TRUE
    razones <- c(razones, "Menciona café tostado")
  }
  if (re_hay(RE_ORIGEN, texto) && re_hay(RE_CAFE, texto)) {
    score <- score + 12
    razones <- c(razones, "Habla de origen, arábica o especialidad")
  }
  if (re_hay(RE_INSUMOS, texto)) {
    score <- score + 18
    razones <- c(razones, "Compra de café o insumos de cafetería")
  }
  if (re_hay(RE_INSTANTANEO, texto) || any(unspsc %in% UNSPSC_CAFE_INSTANTANEO)) {
    score <- score + 22
    razones <- c(razones, "Pide café instantáneo o tipo Nescafé (equivalente posible, no es tu fuerte)")
  }
  if (re_hay(RE_SERVICIO, texto)) {
    score <- score + 20
    razones <- c(razones, "Es un servicio de coffee break o catering")
  }
  if (re_hay(RE_MAQUINA, texto) || any(unspsc %in% UNSPSC_EQUIPO_CAFE)) {
    score <- score + 6
    razones <- c(razones, "Incluye cafetera, molino o máquina en comodato")
  }
  if (any(unspsc %in% UNSPSC_SERVICIO_CAFE) && !encaja) {
    score <- score + 6
    razones <- c(razones, "Código de servicio de cafetería/catering")
  }
  if (encaja && !re_hay(RE_SERVICIO, texto)) {
    score <- score + 10
    razones <- c(razones, "Encaja con suministro de café (tu rubro)")
  }

  oferta$puntaje <- max(0, min(100, score))
  oferta$encaja_producto <- encaja
  oferta$categoria <- categoria_de(oferta$puntaje, texto, encaja)
  oferta$razones <- if (length(razones)) paste(razones, collapse = " | ") else "Mención débil de café"
  oferta
}

oferta_vacia <- function() {
  list(
    fuente = "",
    codigo = "",
    nombre = "",
    estado = "",
    organismo = "",
    region = "",
    comuna = "",
    fecha_cierre = "",
    fecha_publicacion = "",
    monto = NA_real_,
    moneda = "CLP",
    puntaje = 0,
    categoria = "descartada",
    razones = "",
    productos = list(),
    descripcion = "",
    url = "",
    encaja_producto = FALSE
  )
}

oferta_desde_compra_agil <- function(item, detalle = NULL) {
  data <- detalle %||% item
  oferta <- oferta_vacia()
  oferta$fuente <- "compra_agil"
  oferta$codigo <- as_chr(data$codigo %||% item$codigo)
  oferta$nombre <- as_chr(data$nombre %||% item$nombre)
  oferta$estado <- pluck_chr(data, "estado", "glosa")
  if (!nzchar(oferta$estado)) {
    oferta$estado <- pluck_chr(data, "estado", "codigo")
  }
  oferta$organismo <- pluck_chr(data, "institucion", "organismo_comprador")
  if (!nzchar(oferta$organismo)) {
    oferta$organismo <- pluck_chr(item, "institucion", "organismo_comprador")
  }
  oferta$region <- pluck_chr(data, "institucion", "nombre_region")
  oferta$fecha_cierre <- pluck_chr(data, "fechas", "fecha_cierre")
  if (!nzchar(oferta$fecha_cierre)) {
    oferta$fecha_cierre <- pluck_chr(item, "fechas", "fecha_cierre")
  }
  oferta$fecha_publicacion <- pluck_chr(data, "fechas", "fecha_publicacion")
  monto <- pluck_num(data, "presupuesto", "monto_disponible_clp")
  if (is.na(monto)) {
    monto <- pluck_num(data, "montos", "monto_disponible_clp")
  }
  if (is.na(monto)) {
    monto <- pluck_num(item, "montos", "monto_disponible_clp")
  }
  oferta$monto <- monto
  oferta$moneda <- pluck_chr(data, "presupuesto", "moneda")
  if (!nzchar(oferta$moneda)) {
    oferta$moneda <- "CLP"
  }
  oferta$descripcion <- as_chr(data$descripcion)
  oferta$productos <- productos_desde_compra_agil(data)
  oferta$url <- paste0(PORTAL_COMPRA_AGIL, oferta$codigo)
  puntuar(oferta)
}

oferta_desde_licitacion <- function(resumen, detalle = NULL) {
  data <- detalle %||% resumen
  oferta <- oferta_vacia()
  oferta$fuente <- "licitacion"
  oferta$codigo <- as_chr(data$CodigoExterno %||% resumen$CodigoExterno)
  oferta$nombre <- as_chr(data$Nombre %||% resumen$Nombre)
  oferta$estado <- as_chr(data$Estado %||% resumen$CodigoEstado)
  oferta$organismo <- pluck_chr(data, "Comprador", "NombreOrganismo")
  oferta$region <- pluck_chr(data, "Comprador", "RegionUnidad")
  oferta$comuna <- pluck_chr(data, "Comprador", "ComunaUnidad")
  oferta$fecha_cierre <- pluck_chr(data, "Fechas", "FechaCierre")
  if (!nzchar(oferta$fecha_cierre)) {
    oferta$fecha_cierre <- as_chr(data$FechaCierre %||% resumen$FechaCierre)
  }
  oferta$fecha_publicacion <- pluck_chr(data, "Fechas", "FechaPublicacion")
  oferta$monto <- as_num(data$MontoEstimado)
  oferta$moneda <- as_chr(data$Moneda, "CLP")
  oferta$descripcion <- as_chr(data$Descripcion)
  oferta$productos <- productos_desde_licitacion(data)
  oferta$url <- paste0(PORTAL_LICITACION, oferta$codigo)
  puntuar(oferta)
}

filtrar_resumenes_licitacion <- function(rows) {
  Filter(function(row) {
    nombre <- fold(as_chr(row$Nombre))
    if (!re_hay(RE_CAFE, nombre)) {
      return(FALSE)
    }
    if (re_hay(RE_CONCESION, nombre) && !re_hay(RE_INSUMOS, nombre)) {
      return(FALSE)
    }
    if (re_hay(RE_ESPECIALIDAD_MEDICA, nombre) && !grepl("cafe", nombre, fixed = TRUE)) {
      return(FALSE)
    }
    TRUE
  }, rows)
}

parse_cierre <- function(value) {
  text <- trimws(as_chr(value))
  if (!nzchar(text)) {
    return(as.POSIXct(NA))
  }
  text <- gsub("Z$", "", text)
  parsed <- suppressWarnings(as.POSIXct(text, tz = "America/Santiago"))
  parsed
}

sigue_vigente <- function(oferta, hoy = Sys.Date()) {
  cierre <- parse_cierre(oferta$fecha_cierre)
  if (is.na(cierre)) {
    return(TRUE)
  }
  as.Date(cierre) >= hoy
}

necesita_detalle <- function(nombre) {
  !re_hay(RE_SERVICIO, fold(nombre))
}

ofertas_a_tabla <- function(ofertas) {
  if (length(ofertas) == 0) {
    return(data.frame(
      categoria = character(),
      puntaje = integer(),
      codigo = character(),
      nombre = character(),
      organismo = character(),
      region = character(),
      fecha_cierre = character(),
      monto = numeric(),
      fuente = character(),
      url = character(),
      razones = character(),
      stringsAsFactors = FALSE
    ))
  }
  data.frame(
    categoria = vapply(ofertas, function(o) o$categoria, character(1)),
    puntaje = vapply(ofertas, function(o) as.integer(o$puntaje), integer(1)),
    codigo = vapply(ofertas, function(o) o$codigo, character(1)),
    nombre = vapply(ofertas, function(o) o$nombre, character(1)),
    organismo = vapply(ofertas, function(o) o$organismo, character(1)),
    region = vapply(ofertas, function(o) o$region, character(1)),
    fecha_cierre = vapply(ofertas, function(o) o$fecha_cierre, character(1)),
    monto = vapply(ofertas, function(o) as.numeric(o$monto %||% NA_real_), numeric(1)),
    fuente = vapply(ofertas, function(o) o$fuente, character(1)),
    url = vapply(ofertas, function(o) o$url, character(1)),
    razones = vapply(ofertas, function(o) o$razones, character(1)),
    stringsAsFactors = FALSE
  )
}

ordenar_ofertas <- function(ofertas) {
  orden <- c(excelente = 0, buena = 1, regular = 2, servicio = 3, descartada = 4)
  ranks <- vapply(ofertas, function(o) unname(orden[[o$categoria]] %||% 9), numeric(1))
  scores <- vapply(ofertas, function(o) -as.numeric(o$puntaje), numeric(1))
  cierres <- vapply(ofertas, function(o) o$fecha_cierre %||% "9999", character(1))
  ofertas[order(ranks, scores, cierres)]
}

recolectar_ofertas <- function(ticket = NULL,
                               solo_productos = FALSE,
                               max_detalles = 25,
                               log = TRUE) {
  ticket <- ticket_mp(ticket)
  emit <- function(msg) if (isTRUE(log)) message(msg)
  ofertas <- list()

  emit("Buscando compras ágiles abiertas de café...")
  crudas <- list()
  for (q in BUSQUEDAS_COMPRA_AGIL) {
    lote <- tryCatch(compras_agiles(ticket, q), error = function(e) {
      emit(sprintf("  · «%s» falló: %s", q, e$message))
      list()
    })
    emit(sprintf("  · «%s»: %s resultados crudos", q, length(lote)))
    crudas <- c(crudas, lote)
    Sys.sleep(0.3)
  }
  vistos <- character()
  unicas <- list()
  for (row in crudas) {
    codigo <- as_chr(row$codigo)
    if (nzchar(codigo) && !(codigo %in% vistos)) {
      vistos <- c(vistos, codigo)
      unicas <- c(unicas, list(row))
    }
  }
  candidatas <- Filter(function(row) parece_cafe(as_chr(row$nombre)), unicas)
  emit(sprintf("  %s compras ágiles con café en el título (de %s)", length(candidatas), length(unicas)))

  detalles_usados <- 0L
  for (row in candidatas) {
    codigo <- as_chr(row$codigo)
    detalle <- NULL
    if (nzchar(codigo) && necesita_detalle(as_chr(row$nombre)) && detalles_usados < max_detalles) {
      detalle <- tryCatch(compra_agil_detalle(ticket, codigo), error = function(e) {
        emit(sprintf("  detalle %s no disponible: %s", codigo, e$message))
        NULL
      })
      detalles_usados <- detalles_usados + 1L
      Sys.sleep(0.35)
    }
    oferta <- oferta_desde_compra_agil(row, detalle)
    ofertas[[paste0("compra_agil:", oferta$codigo)]] <- oferta
  }

  emit("Revisando licitaciones activas...")
  activas <- licitaciones_activas(ticket)
  resumenes <- filtrar_resumenes_licitacion(activas)
  emit(sprintf("  %s licitaciones con café en el nombre (de %s activas)", length(resumenes), length(activas)))
  for (row in resumenes) {
    codigo <- as_chr(row$CodigoExterno)
    detalle <- NULL
    if (nzchar(codigo) && detalles_usados < max_detalles) {
      detalle <- tryCatch(licitacion_detalle(ticket, codigo), error = function(e) {
        emit(sprintf("  detalle %s no disponible: %s", codigo, e$message))
        NULL
      })
      detalles_usados <- detalles_usados + 1L
      Sys.sleep(0.35)
    }
    oferta <- oferta_desde_licitacion(row, detalle)
    ofertas[[paste0("licitacion:", oferta$codigo)]] <- oferta
  }

  lista <- ordenar_ofertas(unname(ofertas))
  lista <- Filter(function(o) sigue_vigente(o), lista)
  if (isTRUE(solo_productos)) {
    lista <- Filter(function(o) o$categoria %in% c("excelente", "buena", "regular"), lista)
  }
  lista
}
