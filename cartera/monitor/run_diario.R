#!/usr/bin/env Rscript
# Revisión automática diaria: desviaciones + alertas + snapshot JSON
#
#   Rscript cartera/monitor/run_diario.R
#   ALERT_WEBHOOK_URL=... ALERT_EMAIL=... Rscript cartera/monitor/run_diario.R

args_all <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args_all, value = TRUE)
root <- if (length(file_arg) == 1) {
  dirname(normalizePath(sub("^--file=", "", file_arg)))
} else if (file.exists("config.yml")) {
  normalizePath(".")
} else {
  normalizePath("cartera/monitor")
}

source(file.path(root, "lib_monitor.R"), local = TRUE)

cfg <- load_config(root)
result <- run_monitor(cfg)

snap <- result$snap
trades <- result$trades
alert <- result$alert

cat("========================================\n")
cat(" Monitor diario de cartera\n")
cat("========================================\n")
cat("Fecha precios : ", as.character(snap$as_of), "\n", sep = "")
cat("Valor total   : ", scales::dollar(snap$total), "\n", sep = "")
cat("Máx |Δ|       : ", sprintf("%.2f pp", 100 * snap$max_abs_dev), "\n", sep = "")
cat("Suma |Δ|      : ", sprintf("%.2f pp", 100 * snap$sum_abs_dev), "\n", sep = "")
cat("ALERTAS       : ", snap$n_alerta, " | AVISOS: ", snap$n_aviso, "\n", sep = "")
cat("Rebalancear   : ", ifelse(snap$needs_rebalance, "SÍ", "no"), "\n", sep = "")
cat("----------------------------------------\n")

print(
  as.data.frame(snap$tabla %>%
    transmute(
      id, ticker,
      peso = sprintf("%.1f%%", 100 * peso_actual),
      obj = sprintf("%.1f%%", 100 * peso_objetivo),
      d_pp = sprintf("%+.2f", desviacion_pp),
      estado
    )),
  row.names = FALSE
)

if (nrow(trades) > 0) {
  cat("\nAjustes propuestos:\n")
  print(
    as.data.frame(trades %>%
      transmute(
        accion, ticker,
        shares = shares_orden,
        usd = scales::dollar(usd_orden),
        d_pp = sprintf("%+.2f", desviacion_pp)
      )),
    row.names = FALSE
  )
}

cat("\n", alert$summary, "\n", sep = "")
cat("Reporte MD : ", file.path(root, "alertas", "ultima_revision.md"), "\n", sep = "")
cat("Snapshot   : ", file.path(root, "reportes", "ultimo_snapshot.json"), "\n", sep = "")

if (requireNamespace("rmarkdown", quietly = TRUE)) {
  rmd <- file.path(root, "monitor_cartera.Rmd")
  out_html <- file.path(root, "reportes", paste0("monitor_", snap$as_of, ".html"))
  tryCatch({
    rmarkdown::render(
      input = rmd,
      output_file = basename(out_html),
      output_dir = dirname(out_html),
      quiet = TRUE,
      envir = new.env(parent = globalenv())
    )
    cat("HTML       : ", out_html, "\n", sep = "")
  }, error = function(e) {
    cat("HTML no generado: ", conditionMessage(e), "\n", sep = "")
  })
}

quit(status = if (isTRUE(snap$needs_rebalance)) 2 else 0)
