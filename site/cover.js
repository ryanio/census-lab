// The same registry drives the issue navigation and the edition shelf.
const studies = [
  {
    id: "overlap",
    title: "Community overlap",
    nav: "Overlap map",
    theme: "lilac",
    description: (d) =>
      fmt(d.pairs.length) +
      " pairs of collections, mapped by the addresses they share.",
    art: matrixPrint,
  },
  {
    id: "traits",
    title: "Background studies",
    nav: "Trait census",
    theme: "peach",
    description: (d) =>
      fmt(d.colors.length) +
      " background labels, illustrated with NFTs that carry them.",
    art: palettePrint,
  },
  {
    id: "hands",
    title: "Diamond hands",
    nav: "Diamond hands",
    theme: "mint",
    description: (d) =>
      fmt(d.diamond.rows.filter((r) => r.continuous).length) +
      " of " +
      fmt(d.diamond.supply) +
      " Autoglyphs have stayed at their mint address.",
    art: tenurePrint,
  },
];
const hues = [
  "#b79aff",
  "#785bf2",
  "#99baff",
  "#67dbd7",
  "#e5ed93",
  "#f4ab84",
  "#efa5d2",
];
let sectors = [],
  ribbons = [],
  hovered = "";
function thumbnail(parent, w, h) {
  const cv = node("canvas");
  cv.width = w;
  cv.height = h;
  cv.setAttribute("aria-hidden", "true");
  parent.append(cv);
  return cv.getContext("2d");
}
function matrixPrint(parent, d) {
  const keys = Object.keys(d.names),
    n = keys.length,
    ctx = thumbnail(parent, 520, 234);
  const step = Math.min(225 / n, 450 / n),
    max = Math.max(...d.pairs.map((r) => r.shared));
  ctx.translate(260, 116);
  ctx.transform(1.53, 0.25, -0.78, 0.7, 0, 0);
  for (const p of d.pairs) {
    const a = keys.indexOf(p.a),
      b = keys.indexOf(p.b);
    for (const [x, y] of [
      [a, b],
      [b, a],
    ]) {
      const weight = Math.sqrt(p.shared / max);
      ctx.fillStyle = "rgb(220 197 255 / " + (0.13 + 0.87 * weight) + ")";
      ctx.fillRect((x - n / 2) * step, (y - n / 2) * step, step - 1, step - 1);
    }
  }
}
function palettePrint(parent, d) {
  const used = new Set(),
    samples = d.colors
      .filter((r) => {
        if (!r.image || used.has(r.slug)) return false;
        used.add(r.slug);
        return true;
      })
      .slice(0, 8);
  const grid = node("div");
  grid.className = "contact";
  for (const [i, r] of samples.entries()) {
    const cell = node("div");
    cell.style.backgroundColor = hues[i % hues.length];
    const image = node("img");
    image.alt = "";
    image.loading = "lazy";
    image.src = r.image;
    image.onerror = () => image.remove();
    cell.append(image);
    grid.append(cell);
  }
  parent.append(grid);
}
function tenurePrint(parent, d) {
  const ctx = thumbnail(parent, 520, 234),
    rows = [...d.diamond.rows].sort((a, b) => a.token - b.token);
  const cols = Math.ceil(Math.sqrt(rows.length * 2)),
    size = Math.min(460 / cols, 195 / Math.ceil(rows.length / cols));
  ctx.translate(
    (520 - cols * size) / 2,
    (234 - Math.ceil(rows.length / cols) * size) / 2,
  );
  rows.forEach((r, i) => {
    ctx.fillStyle = r.continuous ? "#d3ffaf" : "#40765a";
    const x = (i % cols) * size,
      y = Math.floor(i / cols) * size;
    ctx.fillRect(x, y, size - 2, size - 2);
  });
}
function initCover() {
  el("edition-count").textContent = studies.length + " studies";
  for (const study of studies) {
    const url = "#" + study.id,
      nav = link(study.nav, url);
    nav.dataset.tab = study.id;
    el("publication").append(nav);
    const card = link("", url);
    card.className = "edition-card " + study.theme;
    const print = node("div");
    print.className = "print";
    study.art(print, data);
    const title = node("h3", study.title),
      arrow = node("b", "↗");
    arrow.setAttribute("aria-hidden", "true");
    title.append(arrow);
    card.append(print, title, node("p", study.description(data)));
    el("editions").append(card);
  }
  selector("highlight");
  el("highlight").onchange = () => {
    hovered = "";
    drawAtlas();
  };
  const keys = Object.keys(names),
    weights = new Map(keys.map((s) => [s, 0]));
  for (const p of data.pairs) {
    weights.set(p.a, weights.get(p.a) + p.shared);
    weights.set(p.b, weights.get(p.b) + p.shared);
  }
  const total = [...weights.values()].reduce((a, b) => a + b, 0),
    gap = 0.018,
    unit = total ? (2 * Math.PI - gap * keys.length) / total : 0;
  let angle = -Math.PI / 2;
  sectors = keys.map((slug, i) => {
    const start = angle,
      end = start + weights.get(slug) * unit;
    angle = end + gap;
    return { slug, start, end, color: hues[i % hues.length], cursor: start };
  });
  const bySlug = new Map(sectors.map((a) => [a.slug, a]));
  function segment(s, width) {
    const start = s.cursor;
    s.cursor += width;
    return [start, s.cursor];
  }
  ribbons = data.pairs.map((p) => {
    const a = bySlug.get(p.a),
      b = bySlug.get(p.b);
    return {
      a,
      b,
      amount: p.shared,
      left: segment(a, p.shared * unit),
      right: segment(b, p.shared * unit),
    };
  });
  ribbons.sort((left, right) => left.amount - right.amount);
  const cv = el("ribbons");
  function hit(event) {
    const box = cv.getBoundingClientRect(),
      x = (event.clientX - box.left) / box.width - 0.5,
      y = (event.clientY - box.top) / box.height - 0.5;
    if (Math.hypot(x, y) < 0.32 || Math.hypot(x, y) > 0.49) return "";
    let t = Math.atan2(y, x);
    if (t < -Math.PI / 2) t += 2 * Math.PI;
    return sectors.find((s) => t >= s.start && t <= s.end)?.slug || "";
  }
  cv.onpointermove = (e) => {
    if (e.pointerType === "touch") return;
    const slug = hit(e);
    if (slug !== hovered) {
      hovered = slug;
      drawAtlas();
    }
  };
  cv.onpointerleave = () => {
    if (hovered) {
      hovered = "";
      drawAtlas();
    }
  };
  cv.onclick = (e) => {
    const slug = hit(e);
    if (slug) {
      el("highlight").value = slug;
      hovered = "";
      drawAtlas();
    }
  };
  new ResizeObserver(() => {
    if (!el("home").hidden) drawAtlas();
  }).observe(cv);
}
function drawAtlas() {
  const cv = el("ribbons"),
    size = cv.clientWidth;
  if (!size) return;
  const scale = Math.min(window.devicePixelRatio || 1, 2),
    pixels = Math.round(size * scale);
  if (cv.width !== pixels || cv.height !== pixels) {
    cv.width = pixels;
    cv.height = pixels;
  }
  const c = cv.getContext("2d");
  c.setTransform(pixels / 600, 0, 0, pixels / 600, pixels / 2, pixels / 2);
  c.clearRect(-300, -300, 600, 600);
  const r = 216,
    selection = hovered || el("highlight").value;
  const point = (t, radius) => [Math.cos(t) * radius, Math.sin(t) * radius];
  for (const rad of [239, 251, 279]) {
    c.strokeStyle = "#39353e";
    c.lineWidth = 0.7;
    c.beginPath();
    c.arc(0, 0, rad, 0, 2 * Math.PI);
    c.stroke();
  }
  for (let i = 0; i < 120; i++) {
    const t = (i * Math.PI) / 60;
    c.beginPath();
    c.moveTo(...point(t, 247));
    c.lineTo(...point(t, i % 5 ? 250 : 255));
    c.stroke();
  }
  const active = (e) => selection === e.a.slug || selection === e.b.slug;
  for (const e of [...ribbons].sort(
    (a, b) => Number(active(a)) - Number(active(b)) || a.amount - b.amount,
  )) {
    const [a, b] = e.left,
      [f, g] = e.right;
    c.beginPath();
    c.arc(0, 0, r, a, b);
    c.quadraticCurveTo(0, 0, ...point(f, r));
    c.arc(0, 0, r, f, g);
    c.quadraticCurveTo(0, 0, ...point(a, r));
    c.closePath();
    const gradient = c.createLinearGradient(...point(a, r), ...point(f, r));
    gradient.addColorStop(0, e.a.color);
    gradient.addColorStop(1, e.b.color);
    c.fillStyle = gradient;
    c.globalAlpha = selection ? (active(e) ? 0.95 : 0.055) : 0.68;
    c.fill();
  }
  c.globalAlpha = 1;
  for (const s of sectors) {
    c.beginPath();
    c.arc(0, 0, r + 8, s.start, s.end);
    c.strokeStyle = s.color;
    c.lineWidth = selection === s.slug ? 13 : 8;
    c.stroke();
  }
  const strongest = ribbons.at(-1);
  el("map-link").href =
    "#overlap/" + (el("highlight").value || strongest.a.slug);
  const o = el("readout");
  if (selection) {
    const top = getPairs(selection)[0];
    o.textContent =
      names[selection] +
      " × " +
      names[top.other] +
      " · " +
      fmt(top.n) +
      " shared addresses";
  } else {
    o.textContent =
      Object.keys(names).length +
      " collections · Ribbon width shows shared addresses.";
  }
}
