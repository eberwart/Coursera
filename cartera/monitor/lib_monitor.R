# lib_monitor.R — monitoreo diario de cartera (horizonte 12 meses)

suppressPackageStartupMessages({
  .libPaths(c(path.expand("~/R/library"), .libPaths()))
  library(quantmod)
  library(yaml)
  library(jsonlite)
  library(dplyr)
  library(tidyr)
  library(ggplot2)
  library(scales)
  library(httr)
})

`%||%` <- function(a, b) {
  if (is.null(a)) return(b)
  if (is.character(a) && !nzchar(a)) return(b)
  a
}

.resolve_root <- function() {
  if (exists("MONITOR_DIR", inherits = TRUE)) {
    md <- get("MONITOR_DIR", inherits = TRUE)
    if (nzchar(md)) return(normalizePath(md))
  }
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- grep("^--file=", args, value = TRUE)
  if (length(file_arg) == 1) {
    return(dirname(normalizePath(sub("^--file=", "", file_arg))))
  }
  for (cand in c(".", "monitor", "cartera/monitor")) {
    if (file.exists(file.path(cand, "config.yml"))) return(normalizePath(cand))
  }
  normalizePath(".")
}

load_config <- function(root = NULL) {
  root <- if (is.null(root)) .resolve_root() else normalizePath(root)
  cfg <- yaml::read_yaml(file.path(root, "config.yml"))
  cfg$`_root` <- root
  cfg$activos_df <- do.call(rbind, lapply(cfg$activos, function(x) {
    data.frame(
      id = x$id,
      ticker = x$ticker,
      nombre = x$nombre,
      peso_objetivo = as.numeric(x$peso_objetivo),
      stringsAsFactors = FALSE
    )
  }))
  cfg
}

load_holdings <- function(cfg) {
  path <- file.path(cfg$`_root`, "holdings.csv")
  h <- read.csv(path, stringsAsFactors = FALSE)
  stopifnot(all(c("id", "ticker", "shares") %in% names(h)))
  h$shares <- as.numeric(h$shares)
  h
}

fetch_last_prices <- function(tickers, lookback_days = 20) {
  tickers <- unique(as.character(tickers))
  from <- Sys.Date() - lookback_days
  price <- setNames(rep(NA_real_, length(tickers)), tickers)
  as_of <- setNames(as.Date(rep(NA, length(tickers))), tickers)
  for (tk in tickers) {
    xt <- tryCatch(
      getSymbols(tk, src = "yahoo", from = from, auto.assign = FALSE),
      error = function(e) NULL
    )
    if (is.null(xt) || NROW(xt) == 0) {
      warning("Sin precio para ", tk, call. = FALSE)
      next
    }
    price[tk] <- as.numeric(quantmod::Cl(xt)[NROW(xt)])
    as_of[tk] <- as.Date(zoo::index(xt)[NROW(xt)])
  }
  list(price = price, as_of = as_of)
}

build_snapshot <- function(cfg = NULL) {
  if (is.null(cfg)) cfg <- load_config()
  holdings <- load_holdings(cfg)
  targets <- cfg$activos_df
  px <- fetch_last_prices(targets$ticker)

  snap <- targets %>%
    left_join(holdings %>% select(id, shares), by = "id") %>%
    mutate(
      shares = ifelse(is.na(shares), 0, as.numeric(shares)),
      precio = as.numeric(px$price[ticker]),
      precio_fecha = as.Date(px$as_of[ticker]),
      valor = shares * precio
    )

  total <- sum(snap$valor, na.rm = TRUE)
  snap <- snap %>%
    mutate(
      peso_actual = if (total > 0) valor / total else 0,
      desviacion = peso_actual - peso_objetivo,
      desviacion_pp = 100 * desviacion,
      valor_objetivo = total * peso_objetivo,
      ajuste_usd = valor_objetivo - valor,
      ajuste_shares = ifelse(!is.na(precio) & precio > 0, ajuste_usd / precio, NA_real_),
      estado = case_when(
        abs(desviacion) >= cfg$umbral_desviacion ~ "ALERTA",
        abs(desviacion) >= cfg$umbral_aviso ~ "AVISO",
        TRUE ~ "OK"
      )
    ) %>%
    arrange(desc(abs(desviacion)))

  max_abs <- max(abs(snap$desviacion), na.rm = TRUE)
  sum_abs <- sum(abs(snap$desviacion), na.rm = TRUE)

  list(
    as_of = suppressWarnings(max(snap$precio_fecha, na.rm = TRUE)),
    total = total,
    umbral = cfg$umbral_desviacion,
    umbral_aviso = cfg$umbral_aviso,
    umbral_total = cfg$umbral_desviacion_total,
    tabla = snap,
    max_abs_dev = max_abs,
    sum_abs_dev = sum_abs,
    n_alerta = sum(snap$estado == "ALERTA"),
    n_aviso = sum(snap$estado == "AVISO"),
    needs_rebalance = isTRUE(max_abs >= cfg$umbral_desviacion) ||
      isTRUE(sum_abs >= cfg$umbral_desviacion_total)
  )
}

propose_trades <- function(snap, min_trade_usd = 100) {
  snap$tabla %>%
    filter(!is.na(ajuste_usd), abs(ajuste_usd) >= min_trade_usd) %>%
    mutate(
      accion = ifelse(ajuste_usd > 0, "COMPRAR", "VENDER"),
      shares_orden = abs(round(ajuste_shares, 4)),
      usd_orden = abs(round(ajuste_usd, 2))
    ) %>%
    select(
      id, ticker, nombre, estado, peso_actual, peso_objetivo, desviacion_pp,
      accion, shares_orden, usd_orden, precio
    )
}

plot_desviaciones <- function(snap) {
  df <- snap$tabla
  df$id <- factor(df$id, levels = rev(df$id[order(df$desviacion)]))
  ggplot(df, aes(x = id, y = desviacion_pp, fill = estado)) +
    geom_col(width = 0.7) +
    geom_hline(
      yintercept = c(-100 * snap$umbral, 100 * snap$umbral),
      linetype = "dashed", color = "grey30"
    ) +
    geom_hline(yintercept = 0, linewidth = 0.3) +
    coord_flip() +
    scale_fill_manual(values = c(OK = "#2a9d8f", AVISO = "#e9c46a", ALERTA = "#e76f51")) +
    labs(
      title = paste0("Desviaciones vs objetivo — ", snap$as_of),
      subtitle = paste0(
        "Valor: ", dollar(snap$total),
        " · umbral alerta ±", 100 * snap$umbral, " pp"
      ),
      x = NULL, y = "Desviación (puntos porcentuales)", fill = NULL
    ) +
    theme_minimal(base_size = 12) +
    theme(legend.position = "bottom")
}

plot_pesos <- function(snap) {
  df <- snap$tabla %>%
    select(id, Actual = peso_actual, Objetivo = peso_objetivo) %>%
    pivot_longer(-id, names_to = "tipo", values_to = "peso")
  ggplot(df, aes(x = id, y = peso, fill = tipo)) +
    geom_col(position = position_dodge(width = 0.7), width = 0.65) +
    scale_y_continuous(labels = percent_format(accuracy = 1)) +
    scale_fill_manual(values = c(Actual = "#264653", Objetivo = "#2a9d8f")) +
    labs(title = "Pesos actuales vs objetivo", x = NULL, y = NULL, fill = NULL) +
    theme_minimal(base_size = 12) +
    theme(legend.position = "bottom")
}

format_alert_md <- function(snap, trades) {
  lines <- c(
    paste0("# Alerta de cartera — ", snap$as_of),
    "",
    paste0("- Valor total: **", dollar(snap$total), "**"),
    paste0("- Máx |desviación|: **", sprintf("%.2f pp", 100 * snap$max_abs_dev), "**"),
    paste0("- Suma |desviaciones|: **", sprintf("%.2f pp", 100 * snap$sum_abs_dev), "**"),
    paste0("- Activos en ALERTA: **", snap$n_alerta, "** · en AVISO: **", snap$n_aviso, "**"),
    paste0("- ¿Rebalancear?: **", ifelse(snap$needs_rebalance, "SÍ", "no"), "**"),
    "",
    "## Desviaciones",
    "",
    "| Activo | Peso actual | Objetivo | Δ pp | Estado |",
    "|---|---:|---:|---:|---|"
  )
  for (i in seq_len(nrow(snap$tabla))) {
    r <- snap$tabla[i, ]
    lines <- c(lines, sprintf(
      "| %s | %.1f%% | %.1f%% | %+.2f | %s |",
      r$id, 100 * r$peso_actual, 100 * r$peso_objetivo, r$desviacion_pp, r$estado
    ))
  }
  lines <- c(lines, "", "## Ajustes propuestos", "")
  if (nrow(trades) == 0) {
    lines <- c(lines, "_Sin operaciones por encima del mínimo ($100)._")
  } else {
    lines <- c(
      lines,
      "| Acción | Ticker | Shares | USD | Δ pp |",
      "|---|---|---:|---:|---:|"
    )
    for (i in seq_len(nrow(trades))) {
      r <- trades[i, ]
      lines <- c(lines, sprintf(
        "| %s | %s | %s | %s | %+.2f |",
        r$accion, r$ticker, r$shares_orden, dollar(r$usd_orden), r$desviacion_pp
      ))
    }
  }
  lines <- c(
    lines, "",
    "## Nota",
    "Commodities/cobre permanecen en **0%** (decisión táctica).",
    "Actualiza `holdings.csv` después de ejecutar órdenes.",
    ""
  )
  paste(lines, collapse = "\n")
}

append_history <- function(snap, cfg) {
  path <- file.path(cfg$`_root`, "historial_desviaciones.csv")
  row <- data.frame(
    fecha = as.character(snap$as_of),
    generado = as.character(Sys.time()),
    valor_total = snap$total,
    max_abs_dev_pp = round(100 * snap$max_abs_dev, 4),
    sum_abs_dev_pp = round(100 * snap$sum_abs_dev, 4),
    n_alerta = snap$n_alerta,
    n_aviso = snap$n_aviso,
    needs_rebalance = snap$needs_rebalance,
    stringsAsFactors = FALSE
  )
  if (file.exists(path)) {
    write.table(row, path, sep = ",", row.names = FALSE, col.names = FALSE, append = TRUE)
  } else {
    write.csv(row, path, row.names = FALSE)
  }
  invisible(path)
}

send_webhook <- function(text, url = NULL) {
  url <- url %||% Sys.getenv("ALERT_WEBHOOK_URL", "")
  if (!nzchar(url)) return(invisible(FALSE))
  body <- if (grepl("discord", url, ignore.case = TRUE)) {
    list(content = substr(text, 1, 1900))
  } else {
    list(text = text)
  }
  tryCatch({
    httr::POST(url, body = body, encode = "json")
    TRUE
  }, error = function(e) {
    warning("Webhook falló: ", conditionMessage(e), call. = FALSE)
    FALSE
  })
}

send_email_alert <- function(subject, body, to = NULL) {
  to <- to %||% Sys.getenv("ALERT_EMAIL", "")
  if (!nzchar(to)) return(invisible(FALSE))
  tmp <- tempfile(fileext = ".txt")
  writeLines(body, tmp)
  on.exit(unlink(tmp), add = TRUE)
  cmd <- sprintf("mail -s %s %s < %s", shQuote(subject), shQuote(to), shQuote(tmp))
  tryCatch(system(cmd) == 0, error = function(e) FALSE)
}

write_alert_if_needed <- function(snap, trades, cfg) {
  dir.create(file.path(cfg$`_root`, "alertas"), showWarnings = FALSE, recursive = TRUE)
  md <- format_alert_md(snap, trades)
  writeLines(md, file.path(cfg$`_root`, "alertas", "ultima_revision.md"))

  alert_path <- NULL
  if (isTRUE(cfg$alertas$escribir_archivo) && isTRUE(snap$needs_rebalance)) {
    alert_path <- file.path(cfg$`_root`, "alertas", paste0("alerta_", snap$as_of, ".md"))
    writeLines(md, alert_path)
  }

  summary_txt <- sprintf(
    "Cartera %s | total %s | maxΔ %.2f pp | alertas %d | rebalancear: %s",
    snap$as_of, dollar(snap$total), 100 * snap$max_abs_dev,
    snap$n_alerta, ifelse(snap$needs_rebalance, "SÍ", "no")
  )

  if (isTRUE(snap$needs_rebalance)) {
    send_webhook(paste0("⚠️ ", summary_txt, "\n"), cfg$alertas$webhook_url %||% "")
    send_email_alert(paste0("[Cartera] Desviación ", snap$as_of), md, cfg$alertas$email %||% "")
  }

  list(path = alert_path, summary = summary_txt, markdown = md)
}

run_monitor <- function(cfg = NULL) {
  if (is.null(cfg)) cfg <- load_config()
  snap <- build_snapshot(cfg)
  trades <- propose_trades(snap)
  append_history(snap, cfg)
  alert <- write_alert_if_needed(snap, trades, cfg)

  dir.create(file.path(cfg$`_root`, "reportes"), showWarnings = FALSE, recursive = TRUE)
  payload <- list(
    as_of = as.character(snap$as_of),
    total = snap$total,
    needs_rebalance = snap$needs_rebalance,
    max_abs_dev_pp = unbox(100 * snap$max_abs_dev),
    sum_abs_dev_pp = unbox(100 * snap$sum_abs_dev),
    weights = snap$tabla %>%
      select(id, ticker, shares, precio, valor, peso_actual, peso_objetivo, desviacion_pp, estado),
    trades = trades
  )
  for (fname in c(paste0("snapshot_", snap$as_of, ".json"), "ultimo_snapshot.json")) {
    jsonlite::write_json(
      payload,
      file.path(cfg$`_root`, "reportes", fname),
      pretty = TRUE, auto_unbox = TRUE, dataframe = "rows"
    )
  }
  list(snap = snap, trades = trades, alert = alert, cfg = cfg)
}
