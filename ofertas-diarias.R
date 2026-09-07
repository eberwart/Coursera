#!/usr/bin/env Rscript
# Uso diario sin RMarkdown:
#   MERCADO_PUBLICO_TICKET=tu-ticket Rscript ofertas-diarias.R

args <- commandArgs(trailingOnly = FALSE)
file_arg <- sub("^--file=", "", args[grepl("^--file=", args)])
root <- if (length(file_arg)) dirname(normalizePath(file_arg)) else getwd()
setwd(root)

if (!requireNamespace("httr", quietly = TRUE) || !requireNamespace("jsonlite", quietly = TRUE)) {
  stop("Instala paquetes: install.packages(c('httr', 'jsonlite'))", call. = FALSE)
}

source(file.path("r", "crl_ofertas.R"), encoding = "UTF-8")
ofertas <- recolectar_ofertas(solo_productos = FALSE, max_detalles = 25, log = TRUE)
tabla <- ofertas_a_tabla(ofertas)
tabla <- subset(tabla, categoria != "descartada")

dir.create("reportes", showWarnings = FALSE)
csv_path <- file.path("reportes", paste0("ofertas-", format(Sys.Date(), "%Y-%m-%d"), ".csv"))
write.csv(tabla, csv_path, row.names = FALSE, fileEncoding = "UTF-8")
write.csv(tabla, file.path("reportes", "ofertas-hoy.csv"), row.names = FALSE, fileEncoding = "UTF-8")

insumos <- subset(tabla, categoria %in% c("excelente", "buena", "regular"))
cat("\n=== Café e insumos ===\n")
print(insumos[, c("categoria", "puntaje", "codigo", "nombre", "organismo", "fecha_cierre", "monto")], row.names = FALSE)
cat("\nCSV:", csv_path, "\n")
