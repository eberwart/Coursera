# Pruebas de puntaje (sin API). Desde la raíz del repo:
#   Rscript tests/test_crl_ofertas.R

source("r/crl_ofertas.R", encoding = "UTF-8")

check <- function(cond, msg) {
  if (!isTRUE(cond)) {
    stop(msg, call. = FALSE)
  }
  message("OK: ", msg)
}

check(parece_cafe("COMPRA DE CAFÉ Y ACCESORIOS DE MESA"), "acepta café")
check(parece_cafe("INSUMOS DE CAFETERIA Y BODEGA"), "acepta cafetería")
check(parece_cafe("Servicio de Coffe Break CRM"), "acepta coffe break")
check(!parece_cafe("MATERIALES MEJORAMIENTO DE PARED"), "rechaza muro")
check(
  !parece_cafe("SERVICIOS MEDICOS DE CIRUGIA ESPECIALIDAD TRAUMATOLOGÍA DE CADERA"),
  "rechaza especialidad médica"
)

excelente <- oferta_desde_compra_agil(
  list(codigo = "635-450-COT26", nombre = "CAFÉ Y CAFETERA"),
  list(
    codigo = "635-450-COT26",
    nombre = "COTIZACION DE MOLEDOR ELECTRICO, CAFÉ Y CAFETERA",
    descripcion = "1 kilo de café de especialidad de granos y 1 cafetera",
    estado = list(glosa = "Publicada", codigo = "publicada"),
    institucion = list(organismo_comprador = "SERVICIO DE SALUD DE ARICA", nombre_region = "Arica"),
    fechas = list(fecha_cierre = "2026-08-21 01:13"),
    presupuesto = list(monto_disponible_clp = 212940, moneda = "CLP"),
    productos_solicitados = list(list(
      codigo_producto = "50201706",
      nombre = "Café",
      descripcion = "1 KILO DE CAFÉ DE ESPECIALIDAD DE GRANOS SELECTOS, TOSTADOS A LA PERFECCIÓN",
      cantidad = 1,
      unidad_medida = "KG"
    ))
  )
)
check(excelente$puntaje >= 70, "especialidad en grano tiene puntaje alto")
check(identical(excelente$categoria, "excelente"), "categoría excelente")
check(isTRUE(excelente$encaja_producto), "encaja producto")

nescafe <- oferta_desde_compra_agil(
  list(codigo = "1976-93-COT26", nombre = "TARROS DE CAFE Y VASOS DESECHABLES"),
  list(
    codigo = "1976-93-COT26",
    nombre = "TARROS DE CAFE Y VASOS DESECHABLES",
    descripcion = "tarros de café similar a Nescafé 400 gr",
    estado = list(codigo = "publicada", glosa = "Publicada"),
    productos_solicitados = list(list(
      codigo_producto = "50201709",
      nombre = "Café instantáneo",
      descripcion = "TARRO DE CAFÉ SIMILAR A NESCAFE 400 GR",
      cantidad = 10,
      unidad_medida = "EA"
    ))
  )
)
check(identical(nescafe$categoria, "regular"), "Nescafé es regular")

servicio <- oferta_desde_compra_agil(
  list(codigo = "x", nombre = "SERVICIO COFFE BREAK ESTUDIANTES"),
  list(
    codigo = "1058758-155-COT26",
    nombre = "SERVICIO COFFE BREAK ESTUDIANTES POSTGRADOS MBA ARICA",
    descripcion = "Servicio de Coffe Break para 13 personas",
    estado = list(codigo = "publicada", glosa = "Publicada"),
    productos_solicitados = list(list(
      codigo_producto = "90111603",
      nombre = "Salas de reuniones o banquetes",
      descripcion = "Servicio de Coffe Break"
    ))
  )
)
check(identical(servicio$categoria, "servicio"), "coffee break es servicio")

concesion <- oferta_desde_compra_agil(list(
  codigo = "1",
  nombre = "Concesión de Cafetería para El Hospital San José",
  estado = list(codigo = "publicada", glosa = "Publicada")
))
check(identical(concesion$categoria, "descartada"), "concesión se descarta")

rows <- list(
  list(CodigoExterno = "a", Nombre = "INSUMOS DE CAFETERIA PARA HOSPITAL"),
  list(CodigoExterno = "b", Nombre = "Concesión de Cafetería para El Hospital"),
  list(CodigoExterno = "c", Nombre = "SERVICIOS MEDICOS ESPECIALIDAD TRAUMATOLOGÍA")
)
filtradas <- filtrar_resumenes_licitacion(rows)
check(length(filtradas) == 1 && identical(filtradas[[1]]$CodigoExterno, "a"), "filtra licitaciones")

vieja <- oferta_vacia()
vieja$fecha_cierre <- "2026-04-23 12:01"
vigente <- oferta_vacia()
vigente$fecha_cierre <- "2026-08-21 10:00"
check(!sigue_vigente(vieja, as.Date("2026-08-20")), "cierre viejo")
check(sigue_vigente(vigente, as.Date("2026-08-20")), "cierre vigente")

message("Todas las pruebas R pasaron.")
