(() => {
  const $ = (sel, el = document) => el.querySelector(sel);
  const $$ = (sel, el = document) => [...el.querySelectorAll(sel)];

  const STORAGE = "guardianes-v1";

  const defaultState = () => ({
    screen: "splash",
    tab: "home",
    name: "",
    keys: { 1: null, 2: null, 3: null, 4: null, 5: null },
    bitacora: [],
    reflections: {},
    play: null,
  });

  let state = load() || defaultState();
  let toastTimer = 0;

  function load() {
    try {
      const raw = localStorage.getItem(STORAGE);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }

  function save() {
    localStorage.setItem(STORAGE, JSON.stringify(state));
  }

  function esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function clp(n) {
    const v = Number(n) || 0;
    return "$" + Math.round(v).toLocaleString("es-CL");
  }

  function shuffle(arr) {
    const a = [...arr];
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }

  function station(id) {
    return GAME.stations.find((s) => s.id === id);
  }

  function doneCount() {
    return Object.values(state.keys).filter(Boolean).length;
  }

  function allDone() {
    return doneCount() === 5;
  }

  function clock() {
    const d = new Date();
    return d.toLocaleTimeString("es-CL", { hour: "2-digit", minute: "2-digit", hour12: false });
  }

  function toast(msg) {
    clearTimeout(toastTimer);
    const el = $("#toast");
    el.textContent = msg;
    el.hidden = false;
    toastTimer = setTimeout(() => {
      el.hidden = true;
    }, 2200);
  }

  function confetti() {
    const box = $("#confetti");
    box.innerHTML = "";
    const bits = ["✦", "★", "●", "◆", "💰", "🔑"];
    for (let i = 0; i < 18; i++) {
      const n = document.createElement("i");
      n.textContent = bits[i % bits.length];
      n.style.left = 8 + Math.random() * 84 + "%";
      n.style.animationDelay = Math.random() * 0.4 + "s";
      box.appendChild(n);
    }
    setTimeout(() => {
      box.innerHTML = "";
    }, 2000);
  }

  function go(screen, extra) {
    const t = $("#toast");
    if (t) t.hidden = true;
    const c = $("#confetti");
    if (c) c.innerHTML = "";
    state.screen = screen;
    if (["home", "vault", "bitacora"].includes(screen)) state.tab = screen;
    if (extra) Object.assign(state, extra);
    save();
    render();
  }

  function setKey(id, value) {
    if (!state.keys[id]) {
      state.keys[id] = value;
      save();
      confetti();
    } else {
      state.keys[id] = value;
      save();
    }
  }

  function logEntry(title, body) {
    state.bitacora.unshift({
      t: Date.now(),
      title,
      body,
    });
    save();
  }

  function parseMoney(str) {
    const n = String(str || "").replace(/[^\d]/g, "");
    return n ? Number(n) : NaN;
  }

  function startStation(id) {
    const s = station(id);
    let play = { id, step: "intro" };
    if (id === 1) {
      play.queue = shuffle(GAME.cards.map((c) => c.id));
      play.index = 0;
      play.answers = {};
      play.reasons = {};
    }
    if (id === 2) {
      play.calcs = {
        A: { extra: "", weeks: "" },
        B: { extra: "", weeks: "" },
        C: { extra: "", weeks: "" },
      };
      play.choice = null;
      play.why = "";
    }
    if (id === 3) {
      play.assign = { ahorro: null, gasto: null, compartir: null };
      play.pickedChip = null;
      play.meta = "";
      play.why = "";
    }
    if (id === 4) {
      play.risks = shuffle(GAME.pairs.map((p) => p.id));
      play.prots = shuffle(GAME.pairs.map((p) => p.id));
      play.selRisk = null;
      play.matched = [];
      play.wrong = null;
    }
    if (id === 5) {
      play.b = "";
      play.diff = "";
      play.signals = [false, false, false, false];
    }
    state.play = play;
    state.tab = "home";
    go("station");
  }

  function header(s) {
    return `
      <div class="row between" style="margin-bottom:8px">
        <button class="icon-btn" data-act="home" aria-label="Volver">←</button>
        <div style="text-align:center">
          <div class="tiny">Expediente ${s.code}</div>
          <strong>${esc(s.title)}</strong>
        </div>
        <div style="width:40px"></div>
      </div>
      <div class="progress"><i style="width:${progressFor(s.id)}%"></i></div>
    `;
  }

  function progressFor(id) {
    const p = state.play;
    if (!p || p.id !== id) return state.keys[id] ? 100 : 0;
    if (p.step === "intro") return 8;
    if (p.step === "feedback") return 100;
    if (id === 1) {
      const total = 8 + 1;
      return Math.round(((p.index + (p.step === "reasons" ? 8 : 0)) / total) * 90);
    }
    if (id === 4) return Math.round((p.matched.length / 6) * 90);
    return 45;
  }

  function renderSplash() {
    return `
      <div class="splash" data-act="begin">
        <div class="badge">G</div>
        <div class="tiny" style="opacity:.7">Agencia escolar</div>
        <h1>Guardianes del<br>bienestar financiero</h1>
        <p>5 expedientes · 1 sobre con espejo</p>
        <div class="course">${GAME.course}</div>
        <div class="space-lg"></div>
        <button class="btn gold" data-act="begin">Entrar a la agencia</button>
      </div>
    `;
  }

  function renderOnboard() {
    return `
      <div class="pad" style="padding-top:28px">
        <div class="tiny">Credencial de agente</div>
        <h1 style="margin:8px 0 10px">¿Cómo te llamas?</h1>
        <p class="note">Tu nombre aparece en la bitácora y en el expediente final.</p>
        <div class="space"></div>
        <input class="field" id="name" maxlength="24" placeholder="Ej: Matías, Sofía…" value="${esc(state.name)}" />
        <div class="space-lg"></div>
        <button class="btn primary" data-act="save-name">Recibir credencial</button>
      </div>
    `;
  }

  function renderHome() {
    const n = state.name || "agente";
    const folders = GAME.stations
      .map((s) => {
        const got = state.keys[s.id];
        return `
          <button class="folder ${s.id === 5 ? "wide" : ""}" data-act="open" data-id="${s.id}" style="--c:${s.color}">
            <span class="folder-bar" style="background:${s.color}"></span>
            <div>
              <div class="num">EXPEDIENTE ${s.code}</div>
              <span class="emo">${s.emoji}</span>
              <h3>${esc(s.short)}</h3>
              <div class="tag ${got ? "on" : ""}">${got ? "Clave: " + esc(got) : "Sin resolver"}</div>
            </div>
          </button>
        `;
      })
      .join("");

    return `
      <div class="hero">
        <div class="hello">Hola, ${esc(n)}</div>
        <h1>Tu mesa de expedientes</h1>
        <p class="note" style="color:rgba(255,255,255,.75)">Resuelve las 5 estaciones y abre el sobre final.</p>
        <div class="keys-row">
          ${[1, 2, 3, 4, 5]
            .map(
              (i) =>
                `<div class="key-chip ${state.keys[i] ? "on" : ""}">${state.keys[i] ? esc(state.keys[i]) : "0" + i}</div>`
            )
            .join("")}
        </div>
      </div>
      <div class="pad">
        <div class="grid-2">${folders}</div>
        <button class="vault-cta" data-act="vault">
          <strong>${allDone() ? "Abrir el sobre con espejo" : "Sobre sellado"}</strong>
          <span>${doneCount()}/5 claves reunidas</span>
        </button>
      </div>
    `;
  }

  function renderVault() {
    const pieces = [
      state.keys[1] || "••••",
      state.keys[2] || "•",
      state.keys[3] || "•-•-•",
      state.keys[4] || "••••••",
      state.keys[5] || "•",
    ];
    return `
      <div class="pad" style="padding-top:18px">
        <div class="tiny">Caja fuerte</div>
        <h1 style="margin:6px 0 8px">Claves del sobre</h1>
        <p class="note">Cada estación entrega un fragmento. Cuando estén las cinco, se abre el sobre con espejo.</p>
        <div class="space"></div>
        ${GAME.stations
          .map(
            (s) => `
          <div class="log">
            <div class="tiny">${s.emoji} Expediente ${s.code}</div>
            <strong>${esc(s.title)}</strong>
            <div>${state.keys[s.id] ? "Clave: " + esc(state.keys[s.id]) : "Aún sin resolver"}</div>
          </div>`
          )
          .join("")}
        ${
          allDone()
            ? `<div class="finale">
                <div class="key-reveal">
                  <div class="tiny" style="opacity:.7">Código final</div>
                  <div class="big" style="font-size:22px;line-height:1.35">${esc(pieces.join(" · "))}</div>
                </div>
                <button class="btn gold" data-act="finale">Ver el sobre abierto</button>
              </div>`
            : `<button class="btn ghost" data-act="home">Seguir investigando</button>`
        }
      </div>
    `;
  }

  function renderFinale() {
    const code = [state.keys[1], state.keys[2], state.keys[3], state.keys[4], state.keys[5]].join(" · ");
    return `
      <div class="pad finale">
        <div class="badge" style="margin:8px auto 12px">✓</div>
        <div class="tiny">Misión cumplida</div>
        <h1>El sobre está abierto</h1>
        <p class="note">Agente ${esc(state.name)}, reuniste las cinco claves del bienestar financiero.</p>
        <div class="code-final">${esc(code)}</div>
        <p class="note">DUDA · 7 · tu código % · SEGURO · 6</p>
        <div class="space"></div>
        <div class="feedback" style="text-align:left">
          Dudar de un mensaje raro, comparar antes de comprar, ahorrar al menos lo que gastas, proteger lo tuyo y hacer crecer el dinero en un lugar seguro. Eso es ser guardián.
        </div>
        <div class="space-lg"></div>
        <button class="btn primary" data-act="home">Volver a la mesa</button>
        <div class="space"></div>
        <button class="btn ghost" data-act="reset">Reiniciar misión</button>
      </div>
    `;
  }

  function renderBitacora() {
    const items = state.bitacora.length
      ? state.bitacora
          .map(
            (e) => `
        <div class="log">
          <div class="tiny">${new Date(e.t).toLocaleString("es-CL", { hour: "2-digit", minute: "2-digit", day: "2-digit", month: "short" })}</div>
          <strong>${esc(e.title)}</strong>
          <p class="note">${esc(e.body)}</p>
        </div>`
          )
          .join("")
      : `<p class="note">Todavía no hay notas. Cada estación deja una entrada cuando la resuelves.</p>`;
    return `
      <div class="pad" style="padding-top:18px">
        <div class="tiny">Diario del agente</div>
        <h1 style="margin:6px 0 12px">Bitácora</h1>
        ${items}
        <div class="space"></div>
        <button class="btn ghost" data-act="reset">Reiniciar misión</button>
      </div>
    `;
  }

  function renderStation() {
    const p = state.play;
    if (!p) return renderHome();
    const s = station(p.id);
    if (p.step === "intro") return renderIntro(s);
    if (p.step === "feedback") return renderFeedback(s);
    if (p.id === 1 && p.step === "reasons") return renderReasons(s);
    if (p.id === 1) return renderFraudes(s);
    if (p.id === 2) return renderConsumo(s);
    if (p.id === 3) return renderAhorro(s);
    if (p.id === 4) return renderCuidar(s);
    if (p.id === 5) return renderCrecer(s);
    return renderHome();
  }

  function renderIntro(s) {
    return `
      <div class="pad">
        ${header(s)}
        <div style="font-size:42px">${s.emoji}</div>
        <h2 style="margin:8px 0">${esc(s.title)}</h2>
        <p class="note">${esc(s.intro)}</p>
        <div class="space-lg"></div>
        <button class="btn primary" data-act="play">Empezar estación</button>
        ${state.keys[s.id] ? `<div class="space"></div><button class="btn ghost" data-act="skip-fb">Ver clave ya obtenida</button>` : ""}
      </div>
    `;
  }

  function renderFeedback(s) {
    const talkVal = state.reflections[s.id] || "";
    return `
      <div class="pad">
        ${header(s)}
        <div class="key-reveal">
          <div class="tiny" style="opacity:.7">Clave lista</div>
          <div class="big">${esc(state.keys[s.id] || "—")}</div>
        </div>
        <div class="feedback">${esc(s.feedback)}</div>
        <div class="space"></div>
        <div class="tiny">Para tu bitácora</div>
        <p class="note" style="margin:6px 0 8px">${esc(s.talk)}</p>
        <textarea class="area" id="talk" placeholder="Escribe una idea…">${esc(talkVal)}</textarea>
        <div class="space"></div>
        <button class="btn primary" data-act="save-talk">Guardar y seguir</button>
        <div class="space"></div>
        <button class="btn ghost" data-act="home">Volver sin guardar</button>
      </div>
    `;
  }

  function cardById(id) {
    return GAME.cards.find((c) => c.id === id);
  }

  function renderFraudes(s) {
    const p = state.play;
    const card = cardById(p.queue[p.index]);
    return `
      <div class="pad">
        ${header(s)}
        <div class="between row">
          <div class="tiny">Mensaje ${p.index + 1} de 8</div>
          <div class="note">Desliza o toca</div>
        </div>
        <article class="msg ${card.kind}" id="swipe-card">
          <div class="msg-head">
            <div class="av">${esc(card.handle.slice(0, 1))}</div>
            <div>
              <div>${esc(card.from)}</div>
              <div style="font-size:11px;opacity:.8;font-weight:700">${esc(card.handle)}</div>
            </div>
          </div>
          <div class="msg-body">${esc(card.body)}</div>
          <div class="msg-meta">Tarjeta ${card.id}</div>
        </article>
        <div class="choice">
          <button class="btn alert" data-act="class" data-v="alerta">⚠ ALERTA<small>parece un engaño</small></button>
          <button class="btn ok" data-act="class" data-v="normal">✓ NORMAL<small>contacto o aviso real</small></button>
        </div>
      </div>
    `;
  }

  function renderReasons(s) {
    const p = state.play;
    const alerts = Object.entries(p.answers)
      .filter(([, v]) => v === "alerta")
      .map(([id]) => cardById(Number(id)));
    const list = alerts.length
      ? alerts
          .map(
            (c) => `
          <div class="card">
            <div class="tiny">Tarjeta ${c.id} · ${esc(c.from)}</div>
            <p class="note" style="margin:6px 0">${esc(c.body.slice(0, 90))}${c.body.length > 90 ? "…" : ""}</p>
            <textarea class="area" data-reason="${c.id}" placeholder="¿Por qué te pareció sospechosa?">${esc(p.reasons[c.id] || "")}</textarea>
          </div>`
          )
          .join("")
      : `<p class="note">No marcaste ninguna alerta. Igual puedes enviar tu clasificación.</p>`;
    return `
      <div class="pad">
        ${header(s)}
        <h2>Tu bitácora de alertas</h2>
        <p class="note">En una frase corta, di por qué cada una te pareció sospechosa.</p>
        <div class="space"></div>
        ${list}
        <button class="btn primary" data-act="grade-1">Mostrar al cuartel</button>
      </div>
    `;
  }

  function renderConsumo(s) {
    const p = state.play;
    const opts = GAME.options
      .map((o) => {
        const c = p.calcs[o.id];
        return `
        <div class="card ${p.choice === o.id ? "selected" : ""}">
          <h3>Opción ${o.id} · ${esc(o.title)}</h3>
          <p class="note">${esc(o.text)}</p>
          <div class="calc">
            <div>
              <label>¿Cuánto paga de más?</label>
              <input class="field" inputmode="numeric" data-calc="${o.id}" data-k="extra" placeholder="$" value="${esc(c.extra)}" />
            </div>
            <div>
              <label>¿Cuántas semanas espera?</label>
              <input class="field" inputmode="numeric" data-calc="${o.id}" data-k="weeks" placeholder="semanas" value="${esc(c.weeks)}" />
            </div>
          </div>
          <div class="space"></div>
          <button class="btn ${p.choice === o.id ? "primary" : "ghost"}" data-act="choose" data-v="${o.id}">Elegir ${o.id}</button>
        </div>`;
      })
      .join("");
    return `
      <div class="pad">
        ${header(s)}
        <div class="card" style="background:#fff4e8">
          <div class="tiny">El caso de Tomás</div>
          <p>Zapatillas ${clp(30000)}. Ya tiene ${clp(20000)}. Le faltan ${clp(10000)}. Mesada: ${clp(5000)} / semana.</p>
        </div>
        ${opts}
        <label class="tiny">¿Cuál eligen y por qué?</label>
        <div class="space"></div>
        <textarea class="area" id="why2" placeholder="Escriban su respuesta…">${esc(p.why)}</textarea>
        <div class="space"></div>
        <button class="btn primary" data-act="grade-2">Pedir la clave</button>
      </div>
    `;
  }

  function renderAhorro(s) {
    const p = state.play;
    const cats = [
      ["ahorro", "🐷 Ahorrar", "Para una meta"],
      ["gasto", "🍦 Gastar", "Ahora"],
      ["compartir", "💛 Compartir", "Donar o regalar"],
    ];
    const used = Object.values(p.assign).filter((v) => v != null);
    const buckets = cats
      .map(([k, label, sub]) => {
        const val = p.assign[k];
        const money = val ? clp((GAME.gift * val) / 100) : "—";
        return `
          <button class="bucket ${p.pickedChip && val == null ? "active" : ""}" data-act="drop" data-k="${k}">
            <div class="top"><span>${label}</span><span>${val ? val + "%" : "vacío"}</span></div>
            <div class="note">${sub} · ${money}</div>
          </button>`;
      })
      .join("");
    const chips = GAME.chips
      .map((c) => {
        const cls = used.includes(c) ? "used" : p.pickedChip === c ? "picked" : "";
        return `<button class="chip ${cls}" data-act="chip" data-v="${c}">${c}%</button>`;
      })
      .join("");
    const sum = used.reduce((a, b) => a + b, 0);
    const ready = used.length === 3 && sum === 100;
    return `
      <div class="pad">
        ${header(s)}
        <h2>Reparto de ${clp(GAME.gift)}</h2>
        <p class="note">Elige 3 fichas distintas que sumen 100%. Toca una ficha y luego un cubo. Ahorro ≥ gasto.</p>
        <div class="buckets">${buckets}</div>
        <div class="tiny">Fichas ${sum}% / 100%</div>
        <div class="chip-row">${chips}</div>
        <div class="space"></div>
        <label class="tiny">Meta de ahorro</label>
        <div class="space"></div>
        <input class="field" id="meta" placeholder="Ej: unas zapatillas, un juego…" value="${esc(p.meta)}" />
        <div class="space"></div>
        <textarea class="area" id="why3" placeholder="¿Por qué esta combinación y no otra?">${esc(p.why)}</textarea>
        <div class="space"></div>
        <button class="btn primary" data-act="grade-3" ${ready ? "" : "disabled"}>Pedir la clave</button>
      </div>
    `;
  }

  function renderCuidar(s) {
    const p = state.play;
    const remainingRisks = p.risks.filter((id) => !p.matched.includes(id));
    const remainingProts = p.prots.filter((id) => !p.matched.includes(id));
    const letters = GAME.pairs
      .map(
        (x) =>
          `<span class="${p.matched.includes(x.id) ? "on" : ""}">${p.matched.includes(x.id) ? x.letter : "·"}</span>`
      )
      .join("");
    const risks = remainingRisks
      .map((id) => {
        const x = GAME.pairs.find((p) => p.id === id);
        return `
          <button class="risk ${p.selRisk === id ? "sel" : ""}" data-act="risk" data-id="${id}">
            <span class="ico-lg">${x.riskIcon}</span>
            <span><strong>${id}</strong><br>${esc(x.risk)}</span>
          </button>`;
      })
      .join("");
    const prots = remainingProts
      .map((id) => {
        const x = GAME.pairs.find((p) => p.id === id);
        return `
          <button class="prot ${p.wrong === id ? "wrong" : ""}" data-act="prot" data-id="${id}">
            <span class="ico-lg">${x.protIcon}</span>
            <span><strong>${id.replace("R", "P")}</strong><br>${esc(x.prot)}</span>
          </button>`;
      })
      .join("");
    return `
      <div class="pad">
        ${header(s)}
        <div class="letters">${letters}</div>
        <p class="note">${p.selRisk ? "Ahora elige la protección que corresponde." : "Toca un riesgo rosado y luego su protección verde."}</p>
        <div class="space"></div>
        <div class="tiny">Riesgos</div>
        <div class="space"></div>
        ${risks || "<p class='note'>¡Todas las parejas listas!</p>"}
        <div class="tiny">Protecciones</div>
        <div class="space"></div>
        ${prots}
      </div>
    `;
  }

  function renderCrecer(s) {
    const p = state.play;
    const checks = GAME.signals
      .map(
        (t, i) => `
        <button class="check ${p.signals[i] ? "on" : ""}" data-act="sig" data-i="${i}">
          <span class="box">${p.signals[i] ? "✓" : ""}</span>
          <span>${esc(t)}</span>
        </button>`
      )
      .join("");
    return `
      <div class="pad">
        ${header(s)}
        <div class="pigs">
          <div class="pig">
            <div class="tiny">Chanchito A</div>
            <div style="font-size:28px">🗄</div>
            <strong>Cajón</strong>
            <p class="note">En enero ${clp(50000)}. Lo deja quieto todo el año.</p>
            <div>Diciembre: <strong>${clp(50000)}</strong></div>
          </div>
          <div class="pig">
            <div class="tiny">Chanchito B</div>
            <div style="font-size:28px">🏦</div>
            <strong>Cuenta 5%</strong>
            <p class="note">Mismos ${clp(50000)}, gana un 5% en el año.</p>
            <label class="tiny">¿Cuánto tiene en diciembre?</label>
            <input class="field" id="pigb" inputmode="numeric" placeholder="$52.500" value="${esc(p.b)}" />
          </div>
        </div>
        <div class="space"></div>
        <label class="tiny">Diferencia entre los dos chanchitos</label>
        <div class="space"></div>
        <input class="field" id="diff" inputmode="numeric" placeholder="$2.500" value="${esc(p.diff)}" />
        <div class="offer">
          <div class="tiny">Solo hoy</div>
          <h3>⚡ Oferta especial</h3>
          <p>«Multiplica tu plata en 1 semana. Presta $5.000 a Grupo Ahorro Rápido y en solo 7 días recibes $20.000 ASEGURADO. Cupos limitados. No se lo cuentes a nadie más para que alcances a entrar.»</p>
        </div>
        <div class="tiny">Marca las señales de alerta</div>
        <div class="space"></div>
        ${checks}
        <div class="space"></div>
        <button class="btn primary" data-act="grade-5">Pedir el último dígito</button>
      </div>
    `;
  }

  function chrome(content, showTabs) {
    $("#screen").innerHTML = content;
    $("#tabs").hidden = !showTabs;
    $("#tabs").classList.toggle("visible", showTabs);
    $("#app").classList.toggle("dark", state.screen === "splash");
    $$("#tabs button").forEach((b) => b.classList.toggle("active", b.dataset.tab === state.tab));
    $("#clock").textContent = clock();
  }

  function render() {
    const showTabs = ["home", "vault", "bitacora", "finale"].includes(state.screen);
    let html = "";
    if (state.screen === "splash") html = renderSplash();
    else if (state.screen === "onboard") html = renderOnboard();
    else if (state.screen === "home") html = renderHome();
    else if (state.screen === "vault") html = renderVault();
    else if (state.screen === "bitacora") html = renderBitacora();
    else if (state.screen === "finale") html = renderFinale();
    else if (state.screen === "station") html = renderStation();
    else html = renderHome();
    chrome(html, showTabs && state.screen !== "splash" && state.screen !== "onboard");
    bindSwipe();
    bindFields();
  }

  function bindFields() {
    const name = $("#name");
    if (name) name.addEventListener("keydown", (e) => {
      if (e.key === "Enter") saveName();
    });
    $$("[data-calc]").forEach((inp) => {
      inp.addEventListener("input", () => {
        const id = inp.dataset.calc;
        const k = inp.dataset.k;
        state.play.calcs[id][k] = inp.value;
        save();
      });
    });
    $$("[data-reason]").forEach((inp) => {
      inp.addEventListener("input", () => {
        state.play.reasons[inp.dataset.reason] = inp.value;
        save();
      });
    });
    const why2 = $("#why2");
    if (why2) why2.addEventListener("input", () => { state.play.why = why2.value; save(); });
    const why3 = $("#why3");
    if (why3) why3.addEventListener("input", () => { state.play.why = why3.value; save(); });
    const meta = $("#meta");
    if (meta) meta.addEventListener("input", () => { state.play.meta = meta.value; save(); });
    const pigb = $("#pigb");
    if (pigb) pigb.addEventListener("input", () => { state.play.b = pigb.value; save(); });
    const diff = $("#diff");
    if (diff) diff.addEventListener("input", () => { state.play.diff = diff.value; save(); });
    const talk = $("#talk");
    if (talk) talk.addEventListener("input", () => { state.reflections[state.play.id] = talk.value; save(); });
  }

  function bindSwipe() {
    const card = $("#swipe-card");
    if (!card) return;
    let x0 = 0;
    let dx = 0;
    const start = (x) => { x0 = x; dx = 0; };
    const move = (x) => {
      dx = x - x0;
      card.style.transform = `translateX(${dx}px) rotate(${dx / 28}deg)`;
      card.style.opacity = String(1 - Math.min(0.4, Math.abs(dx) / 280));
    };
    const end = () => {
      if (dx > 80) classify("alerta");
      else if (dx < -80) classify("normal");
      else {
        card.style.transform = "";
        card.style.opacity = "";
      }
    };
    card.addEventListener("touchstart", (e) => start(e.touches[0].clientX), { passive: true });
    card.addEventListener("touchmove", (e) => move(e.touches[0].clientX), { passive: true });
    card.addEventListener("touchend", end);
    card.addEventListener("mousedown", (e) => {
      start(e.clientX);
      const mv = (ev) => move(ev.clientX);
      const up = () => {
        window.removeEventListener("mousemove", mv);
        window.removeEventListener("mouseup", up);
        end();
      };
      window.addEventListener("mousemove", mv);
      window.addEventListener("mouseup", up);
    });
  }

  function saveName() {
    const v = ($("#name")?.value || state.name || "").trim();
    if (v.length < 2) {
      toast("Escribe tu nombre (al menos 2 letras)");
      return;
    }
    state.name = v;
    go("home");
  }

  function classify(v) {
    const p = state.play;
    const id = p.queue[p.index];
    p.answers[id] = v;
    p.index += 1;
    if (navigator.vibrate) navigator.vibrate(12);
    if (p.index >= p.queue.length) p.step = "reasons";
    save();
    render();
  }

  function gradeFraudes() {
    const p = state.play;
    const trueAlerts = GAME.cards.filter((c) => c.alert).map((c) => c.id);
    const marked = Object.entries(p.answers)
      .filter(([, v]) => v === "alerta")
      .map(([id]) => Number(id));
    const hits = trueAlerts.filter((id) => marked.includes(id)).length;
    const reasons = trueAlerts
      .filter((id) => marked.includes(id))
      .map((id) => `#${id}: ${p.reasons[id] || "(sin nota)"}`)
      .join(" · ");
    logEntry("Expediente 01 · Fraudes", `Alertas marcadas: ${marked.join(", ") || "ninguna"}. Aciertos de alerta: ${hits}/4. ${reasons}`);
    if (hits >= 3) {
      setKey(1, GAME.keys[1]);
      p.step = "feedback";
      save();
      render();
      toast("Clave obtenida: DUDA");
    } else {
      toast("Necesitas al menos 3 de las 4 alertas. Intenta de nuevo.");
      startStation(1);
      state.play.step = "play";
      save();
      render();
    }
  }

  function gradeConsumo() {
    const p = state.play;
    $$("[data-calc]").forEach((inp) => {
      p.calcs[inp.dataset.calc][inp.dataset.k] = inp.value;
    });
    const why = $("#why2");
    if (why) p.why = why.value;
    if (!p.choice) {
      toast("Elige una opción (A, B o C)");
      return;
    }
    let mathOk = true;
    for (const o of GAME.options) {
      const extra = parseMoney(p.calcs[o.id].extra);
      const weeks = Number(String(p.calcs[o.id].weeks).replace(/[^\d]/g, ""));
      if (extra !== o.extra || weeks !== o.weeks) mathOk = false;
    }
    if (!mathOk) {
      toast("Revisa los cálculos: extra y semanas de A, B y C.");
      return;
    }
    if (p.choice === "A") {
      toast("A cuesta $3.000 extra. Prueba B o C.");
      return;
    }
    setKey(2, GAME.keys[2]);
    logEntry(
      "Expediente 02 · Consumo",
      `Eligieron ${p.choice}. ${p.why || "Sin comentario."}`
    );
    p.step = "feedback";
    save();
    render();
    toast("Clave obtenida: 7");
  }

  function gradeAhorro() {
    const p = state.play;
    const meta = $("#meta");
    const why = $("#why3");
    if (meta) p.meta = meta.value;
    if (why) p.why = why.value;
    const a = p.assign.ahorro;
    const g = p.assign.gasto;
    const c = p.assign.compartir;
    if ([a, g, c].some((v) => v == null)) {
      toast("Asigna 3 fichas distintas");
      return;
    }
    if (a + g + c !== 100) {
      toast("Las 3 fichas deben sumar 100%");
      return;
    }
    if (a < g) {
      toast("El ahorro debe ser igual o mayor que el gasto");
      return;
    }
    const code = `${a / 10}${g / 10}${c / 10}`;
    setKey(3, code.split("").join("-"));
    logEntry(
      "Expediente 03 · Ahorro",
      `Ahorro ${a}% (${clp((GAME.gift * a) / 100)}) · Gasto ${g}% · Compartir ${c}%. Meta: ${p.meta || "—"}. ${p.why || ""}`
    );
    p.step = "feedback";
    save();
    render();
    toast("Código % obtenido: " + state.keys[3]);
  }

  function tryMatch(protId) {
    const p = state.play;
    if (!p.selRisk) {
      toast("Primero toca un riesgo");
      return;
    }
    if (p.selRisk === protId) {
      p.matched.push(protId);
      p.selRisk = null;
      p.wrong = null;
      if (navigator.vibrate) navigator.vibrate(16);
      if (p.matched.length === 6) {
        setKey(4, GAME.keys[4]);
        logEntry("Expediente 04 · Cuidar lo mío", "Seis parejas correctas. Palabra: SEGURO.");
        p.step = "feedback";
        save();
        render();
        toast("Clave obtenida: SEGURO");
        return;
      }
      save();
      render();
    } else {
      p.wrong = protId;
      save();
      render();
      toast("Esa protección no corresponde. Prueba otra.");
      setTimeout(() => {
        if (state.play) state.play.wrong = null;
      }, 400);
    }
  }

  function gradeCrecer() {
    const p = state.play;
    const pigb = $("#pigb");
    const diff = $("#diff");
    if (pigb) p.b = pigb.value;
    if (diff) p.diff = diff.value;
    const b = parseMoney(p.b);
    const d = parseMoney(p.diff);
    if (b !== 52500 || d !== 2500) {
      toast("Calcula el 5% de $50.000 y súmalo. La diferencia es ese 5%.");
      return;
    }
    if (!p.signals.every(Boolean)) {
      toast("Marca las 4 señales de alerta de la oferta.");
      return;
    }
    setKey(5, GAME.keys[5]);
    logEntry("Expediente 05 · Crecer", `Chanchito B ${clp(52500)}. Diferencia ${clp(2500)}. 4 señales marcadas.`);
    p.step = "feedback";
    save();
    render();
    toast("Dígito obtenido: 6");
  }

  function onClick(e) {
    const t = e.target.closest("[data-act], [data-tab]");
    if (!t) return;
    const act = t.dataset.act;
    const tab = t.dataset.tab;
    if (tab) {
      go(tab);
      return;
    }
    if (act === "begin") {
      go(state.name ? "home" : "onboard");
      return;
    }
    if (act === "save-name") return saveName();
    if (act === "home") return go("home");
    if (act === "vault") return go(allDone() && t.classList.contains("vault-cta") && doneCount() === 5 ? "vault" : "vault");
    if (act === "finale") return go("finale");
    if (act === "open") return startStation(Number(t.dataset.id));
    if (act === "play") {
      state.play.step = "play";
      save();
      render();
      return;
    }
    if (act === "skip-fb") {
      state.play.step = "feedback";
      save();
      render();
      return;
    }
    if (act === "class") return classify(t.dataset.v);
    if (act === "grade-1") return gradeFraudes();
    if (act === "choose") {
      state.play.choice = t.dataset.v;
      save();
      render();
      return;
    }
    if (act === "grade-2") return gradeConsumo();
    if (act === "chip") {
      const v = Number(t.dataset.v);
      const used = Object.values(state.play.assign);
      if (used.includes(v)) {
        const k = Object.keys(state.play.assign).find((key) => state.play.assign[key] === v);
        state.play.assign[k] = null;
        state.play.pickedChip = null;
      } else {
        state.play.pickedChip = state.play.pickedChip === v ? null : v;
      }
      save();
      render();
      return;
    }
    if (act === "drop") {
      const p = state.play;
      if (p.pickedChip == null) {
        if (p.assign[t.dataset.k] != null) {
          p.assign[t.dataset.k] = null;
          save();
          render();
        } else toast("Toca primero una ficha");
        return;
      }
      p.assign[t.dataset.k] = p.pickedChip;
      p.pickedChip = null;
      save();
      render();
      return;
    }
    if (act === "grade-3") return gradeAhorro();
    if (act === "risk") {
      state.play.selRisk = t.dataset.id;
      save();
      render();
      return;
    }
    if (act === "prot") return tryMatch(t.dataset.id);
    if (act === "sig") {
      const i = Number(t.dataset.i);
      state.play.signals[i] = !state.play.signals[i];
      save();
      render();
      return;
    }
    if (act === "grade-5") return gradeCrecer();
    if (act === "save-talk") {
      const val = $("#talk")?.value || "";
      state.reflections[state.play.id] = val;
      if (val.trim()) logEntry("Para conversar · " + station(state.play.id).short, val.trim());
      go("home");
      return;
    }
    if (act === "reset") {
      if (confirm("¿Borrar el progreso de esta misión?")) {
        state = defaultState();
        state.screen = "onboard";
        save();
        render();
      }
    }
  }

  function init() {
    $("#clock").textContent = clock();
    setInterval(() => {
      const c = $("#clock");
      if (c) c.textContent = clock();
    }, 30000);
    document.addEventListener("click", onClick);
    if (!state.screen) state.screen = "splash";
    render();
  }

  init();
})();
