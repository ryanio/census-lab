const data = JSON.parse(document.getElementById("data").textContent),
  names = data.names;
const el = (id) => document.getElementById(id),
  fmt = (n) => n.toLocaleString("en-US");
const node = (tag, text) => {
  const e = document.createElement(tag);
  if (text != null) e.textContent = text;
  return e;
};
function link(text, url) {
  const a = node("a", text);
  a.href = url;
  return a;
}
function selector(id) {
  for (const [slug, name] of Object.entries(names))
    el(id).add(new Option(name, slug));
}
selector("community");
selector("art");
el("date").textContent = new Intl.DateTimeFormat("en-US", {
  day: "numeric",
  month: "short",
  year: "numeric",
  timeZone: "UTC",
}).format(new Date(data.edition + "T00:00:00Z"));
function studyURL(tab, slug) {
  const fragment = "#" + tab + (slug ? "/" + slug : "");
  if (location.protocol === "file:") return fragment;
  return (tab === "home" ? "./" : tab + ".html") + (slug ? fragment : "");
}
function editionURL(tab) {
  return new URL("https://ryanio.github.io/census-lab/editions/" + data.edition + "/" + tab + ".html");
}
async function copyStudyLink(url, status, study) {
  try {
    await navigator.clipboard.writeText(url.href);
    status.textContent = "Link copied";
    trackEvent("share", study, {method: "copy_link", content_type: "study", item_id: study});
  } catch {
    const field = node("input");
    field.readOnly = true;
    field.setAttribute("aria-label", "Share link");
    field.value = url.href;
    status.replaceChildren(field);
    field.select();
  }
}
for (const button of document.querySelectorAll("[data-share-study]")) {
  button.onclick = () => {
    const tab = button.dataset.shareStudy;
    const url = editionURL(tab);
    url.hash = tab + "/" + el(tab === "overlap" ? "community" : "hold-series").value;
    copyStudyLink(url, button.nextElementSibling, tab);
  };
}
function navigate(tab, slug) {
  explore(tab, "switch_collection");
  location.href = studyURL(tab, slug);
}
function getPairs(s) {
  return data.pairs
    .filter((p) => p.a === s || p.b === s)
    .map((p) => ({
      other: p.a === s ? p.b : p.a,
      n: p.shared,
      of: p.a === s ? p.pct_a : p.pct_b,
      back: p.a === s ? p.pct_b : p.pct_a,
      top: p.top100_shared,
    }))
    .sort((a, b) => b.n - a.n || a.other.localeCompare(b.other));
}
const positions = [
  [50, 12],
  [82, 35],
  [76, 79],
  [24, 79],
  [18, 35],
];
function drawNeighbors(s) {
  const list = getPairs(s),
    box = el("map");
  box.replaceChildren();
  const cv = node("canvas");
  box.append(cv);
  const w = box.clientWidth,
    h = box.clientHeight,
    dpr = window.devicePixelRatio || 1;
  cv.width = w * dpr;
  cv.height = h * dpr;
  const ctx = cv.getContext("2d");
  ctx.scale(dpr, dpr);
  ctx.strokeStyle = "#9374cf";
  const center = node("div", names[s]);
  center.className = "node center";
  center.style.left = "50%";
  center.style.top = "48%";
  list.slice(0, 5).forEach((r, i) => {
    const [x, y] = positions[i];
    ctx.lineWidth = 1 + (14 * r.n) / Math.max(1, list[0].n);
    ctx.beginPath();
    ctx.moveTo(w * 0.5, h * 0.48);
    ctx.lineTo((w * x) / 100, (h * y) / 100);
    ctx.stroke();
    const b = node("button", names[r.other]);
    b.className = "node";
    b.style.left = x + "%";
    b.style.top = y + "%";
    b.append(node("small", fmt(r.n) + " shared"));
    b.onclick = () => navigate("overlap", r.other);
    box.append(b);
  });
  box.append(center);
}
function map(s) {
  drawNeighbors(s);
  const list = getPairs(s);
  const headings = [
    ...el("neighbors").closest("table").querySelectorAll("th"),
  ].slice(1);
  const more = el("more-neighbors");
  function neighbors(expanded) {
    const visible = expanded ? list : list.slice(0, 8);
    more.hidden = list.length <= 8;
    more.textContent = expanded
      ? "Show closest eight"
      : "Show all " + list.length + " neighbors";
    more.setAttribute("aria-expanded", String(expanded));
    more.onclick = () => neighbors(!expanded);
    el("neighbors").replaceChildren(
      ...visible.map((r) => {
        const tr = node("tr"),
          cell = node("td"),
          a = link(names[r.other], studyURL("overlap", r.other));
        a.addEventListener("click", () => explore("overlap", "switch_collection"));
        cell.append(a);
        tr.append(
          cell,
          ...[fmt(r.n), r.of + "%", r.back + "%", r.top].map((value, index) => {
            const cell = node("td"),
              label = node("small", headings[index].textContent);
            label.className = "stat-label";
            label.setAttribute("aria-hidden", "true");
            cell.append(label, String(value));
            return cell;
          }),
        );
        return tr;
      }),
    );
  }
  neighbors(false);
}
el("download").onclick = () => {
  const s = el("community").value,
    cv = node("canvas");
  cv.width = 1200;
  cv.height = 670;
  const c = cv.getContext("2d");
  c.fillStyle = "#e9dfff";
  c.fillRect(0, 0, 1200, 670);
  c.fillStyle = "#251a38";
  c.font = "26px sans-serif";
  c.fillText("Census   /   " + data.edition, 60, 70);
  c.font = "52px Georgia";
  c.fillText(names[s], 60, 155, 1080);
  c.font = "26px sans-serif";
  c.fillText("Closest neighbors by shared holder addresses", 60, 212);
  getPairs(s)
    .slice(0, 5)
    .forEach((r, i) => {
      c.fillText(names[r.other], 60, 290 + i * 61, 650);
      c.fillText(fmt(r.n) + " shared   ·   " + r.of + "%", 790, 290 + i * 61);
    });
  c.font = "20px sans-serif";
  c.fillText(
    Object.keys(names).length +
      " Ethereum collections · percentages are of " +
      names[s] +
      " holder addresses",
    60,
    622,
    1080,
  );
  const a = link("", cv.toDataURL());
  a.download = s + "-neighbors.png";
  a.click();
};
function traits(s) {
  const rows = data.colors
      .filter((r) => r.slug === s)
      .sort((a, b) => b.count - a.count),
    palette = el("strips"),
    detail = el("focus");
  palette.replaceChildren();
  detail.replaceChildren();
  palette.hidden = !rows.length;
  palette.style.display = rows.length ? "flex" : "none";
  const choice = el("background-choice");
  choice.closest("label").hidden = !rows.length;
  choice.replaceChildren(...rows.map((r, i) => new Option(r.value, String(i))));
  choice.onchange = () => pick(rows[choice.selectedIndex]);
  function pick(r) {
    choice.selectedIndex = rows.indexOf(r);
    detail.replaceChildren();
    if (r.image) {
      const im = node("img");
      im.alt = "";
      im.src = r.image;
      detail.append(im);
    }
    detail.append(
      node("strong", r.value),
      node("span", fmt(r.count) + " NFTs"),
    );
    if (r.url) detail.append(link("View example", r.url));
  }
  if (rows.length) pick(rows[0]);
  else
    detail.textContent =
      "No matching text background category was returned for this collection.";
  rows.forEach((r) => {
    const b = node("button");
    b.className = "swatch";
    b.title = r.value + " · " + fmt(r.count);
    b.setAttribute("aria-label", b.title);
    b.style.flex = r.count + " 1 0";
    if (r.image)
      b.style.backgroundImage = "url(" + JSON.stringify(r.image) + ")";
    b.onclick = () => pick(r);
    palette.append(b);
  });
  const categories = data.traits[s] || {},
    category = el("category"),
    order = el("trait-order");
  category.replaceChildren(
    ...Object.keys(categories)
      .sort()
      .map((k) => new Option(k, k)),
  );
  if (rows.length && Object.hasOwn(categories, rows[0].category))
    category.value = rows[0].category;
  function rank() {
    const values = [...(categories[category.value] || [])],
      mode = order.value;
    const eligible =
      mode === "floor" ? values.filter((v) => v[2].ETH !== undefined) : values;
    eligible.sort(
      (a, b) =>
        (mode === "floor"
          ? b[2].ETH - a[2].ETH
          : mode === "common"
            ? b[1] - a[1]
            : a[1] - b[1]) || a[0].localeCompare(b[0]),
    );
    const body = el("labels");
    body.replaceChildren();
    for (const [value, count, floors] of eligible.slice(0, 8)) {
      const row = node("tr");
      const prices = Object.entries(floors)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([currency, price]) => price + " " + currency);
      row.append(
        node("td", value),
        node("td", fmt(count)),
        node("td", prices.join(" · ") || "Unlisted"),
      );
      body.append(row);
    }
    if (!eligible.length) {
      const row = node("tr"),
        cell = node(
          "td",
          mode === "floor"
            ? "No ETH listings for this category."
            : "No text traits reported.",
        );
      cell.colSpan = 3;
      row.append(cell);
      body.append(row);
    }
  }
  category.onchange = order.onchange = rank;
  rank();
}
function hands(slug) {
  const d = data.holdings[slug],
    rows = [...d.rows].sort(
      (a, b) => a.since.localeCompare(b.since) || a.token - b.token,
    );
  for (const id of ["metrics", "hist", "longest", "block"])
    el(id).replaceChildren();
  el("holds-download").href =
    slug === "autoglyphs" ? "holds.csv" : slug + "-holds.csv";
  el("holds-download").textContent =
    "Download all " + fmt(d.supply) + " holds (CSV)";
  const continuous = rows.filter((r) => r.continuous).length;
  for (const [n, title] of [
    [d.supply, "tokens verified"],
    [continuous, "unbroken mint holds"],
    [rows.filter((r) => r.returned).length, "returned to mint recipient"],
  ]) {
    const m = node("div");
    m.append(node("b", fmt(n)), node("span", title));
    el("metrics").append(m);
  }
  const bounds = [1, 2, 4, 6, Infinity],
    counts = bounds.map(() => 0);
  for (const r of rows) {
    const years = (d.timestamp - Date.parse(r.since) / 1000) / (365.25 * 86400);
    counts[bounds.findIndex((n) => years < n)]++;
  }
  counts.forEach((n, i) => {
    const bar = node("div");
    bar.className = "bar";
    const ink = node("div");
    ink.className = "ink";
    ink.style.width = (100 * n) / Math.max(...counts) + "%";
    bar.append(
      node(
        "span",
        [
          "Under 1 year",
          "1 to <2 years",
          "2 to <4 years",
          "4 to <6 years",
          "6+ years",
        ][i],
      ),
      ink,
      node("span", fmt(n)),
    );
    el("hist").append(bar);
  });
  for (const r of rows.slice(0, 5)) {
    const tr = node("tr"),
      a = node("td"),
      b = node("td");
    a.append(
      link(
        "#" + r.token,
        "https://opensea.io/assets/ethereum/" + d.contract + "/" + r.token,
      ),
    );
    b.append(
      link(r.since.slice(0, 10), "https://etherscan.io/tx/" + r.transaction),
    );
    tr.append(
      a,
      b,
      node(
        "td",
        r.continuous
          ? "Held since mint"
          : r.returned
            ? "Returned to mint recipient"
            : "Transferred",
      ),
    );
    el("longest").append(tr);
  }
  el("block").append(
    "Replayed " +
      fmt(d.logs) +
      " transfer logs and verified the supply and all " +
      d.supply +
      " owners at ",
    link("block " + fmt(d.block), "https://etherscan.io/block/" + d.hash),
    ".",
  );
}
function render() {
  let [tab, s] = location.hash.slice(1).split("/");
  if (!tab) tab = document.body.dataset.entry;
  if (tab !== "home" && !studies.some((study) => study.id === tab))
    tab = "home";
  if (tab === "hands") {
    if (!Object.hasOwn(data.holdings, s)) s = "autoglyphs";
  } else if (!Object.hasOwn(names, s)) s = "azuki";
  for (const id of ["home", ...studies.map((study) => study.id)])
    el(id).hidden = id !== tab;
  for (const b of document.querySelectorAll("nav [data-tab]"))
    b.setAttribute("aria-current", b.dataset.tab === tab ? "page" : "false");
  document.body.dataset.edition = tab;
  if (tab === "home") drawAtlas();
  if (tab === "overlap") {
    el("community").value = s;
    map(s);
  }
  if (tab === "hands") {
    el("hold-series").value = s;
    hands(s);
  }
  if (tab === "traits") {
    el("art").value = s;
    if (!el("shared-category").options.length) initSharedTraits();
    if (location.hash.startsWith("#traits/")) el("collection-traits").open = true;
    traits(s);
  }
}
el("community").onchange = (e) => navigate("overlap", e.target.value);
el("art").onchange = (e) => navigate("traits", e.target.value);
// Use the same GA4 stream as PFP Census and Card Census on the published site.
function startAnalytics() {
  if (location.origin !== "https://ryanio.github.io") return () => {};
  const id = "G-Y2NGRYCS3V";
  window.dataLayer = window.dataLayer || [];
  function gtag() {
    window.dataLayer.push(arguments);
  }
  gtag("js", new Date());
  gtag("config", id, { send_page_view: false });
  const script = document.createElement("script");
  script.async = true;
  script.src = "https://www.googletagmanager.com/gtag/js?id=" + id;
  document.head.append(script);
  return (event, study, params) => {
    gtag("event", event, { content_group: study, ...params });
  };
}
const trackEvent = startAnalytics();
function explore(study, action) {
  trackEvent("study_explore", study, { study_action: action });
}
let referrer = document.referrer;
function trackEdition(tab) {
  const url = new URL(location.href);
  url.hash = "";
  trackEvent("page_view", tab, {
    page_title: el(tab).querySelector("h1").innerText.replace(/\s+/g, " ").trim(),
    page_location: url.href,
    page_referrer: referrer,
  });
  referrer = url.href;
}
el("holds-download").addEventListener("click", () => explore("hands", "download_csv"));
let lastTab = "";
window.addEventListener("hashchange", () => {
  render();
  const active = document.body.dataset.edition;
  if (lastTab !== active) {
    window.scrollTo(0, 0);
    trackEdition(active);
  }
  lastTab = active;
});
new ResizeObserver(() => {
  if (!el("overlap").hidden) drawNeighbors(el("community").value);
}).observe(el("map"));
document.querySelector(".skip").onclick = (event) => {
  event.preventDefault();
  el("content").focus();
  el("content").scrollIntoView();
};
for (const [slug, series] of Object.entries(data.holdings))
  el("hold-series").add(new Option(series.name, slug));
el("hold-series").onchange = (e) => navigate("hands", e.target.value);
if (location.protocol === "file:")
  document.querySelector("header .brand").href = "#home";
initCover();
render();
lastTab = document.body.dataset.edition;

trackEdition(lastTab);
