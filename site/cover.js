// The same registry drives the issue navigation and the edition shelf.
const studies = [
  {
    id: "overlap",
    title: "Community overlap",
    nav: "Overlap map",
    icon: "network",
    theme: "lilac",
    description: (d) =>
      fmt(d.pairs.length) +
      " pairs of collections, mapped by the addresses they share.",
    art: matrixPrint,
  },
  {
    id: "traits",
    title: "Background studies",
    nav: "Traits",
    icon: "swatch-book",
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
    icon: "gem",
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
    nav.prepend(icon(study.icon));
    nav.dataset.tab = study.id;
    el("publication").append(nav);
    const card = link("", url);
    card.className = "edition-card " + study.theme;
    const print = node("div");
    print.className = "print";
    study.art(print, data);
    const title = node("h3", study.title);
    title.append(icon(study.icon));
    card.append(print, title, node("p", study.description(data)));
    el("editions").append(card);
  }
  selector("highlight");
  initAtlas();
}
