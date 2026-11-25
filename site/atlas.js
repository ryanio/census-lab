const svgNS = "http://www.w3.org/2000/svg";
function svgNode(tag, attrs = {}) {
  const element = document.createElementNS(svgNS, tag);
  for (const [key, value] of Object.entries(attrs))
    element.setAttribute(key, value);
  return element;
}
function icon(name) {
  const image = svgNode("svg", { class: "icon", "aria-hidden": "true" });
  image.append(svgNode("use", { href: "#icon-" + name }));
  return image;
}

// Keep the same paths for drawing and picking. The overlay never intercepts the pointer.
let drawAtlas = () => {};
function initAtlas() {
  const chart = el("ribbons"),
    filter = el("highlight"),
    card = el("hover-card");
  const defs = svgNode("defs"),
    bands = svgNode("g"),
    overlay = svgNode("g", { "pointer-events": "none" }),
    rim = svgNode("g");
  chart.append(defs, bands, overlay, rim);
  const radius = 214,
    gap = 0.018,
    point = (angle, r) => [Math.cos(angle) * r, Math.sin(angle) * r];
  const keys = Object.keys(names),
    sectors = new Map(
      keys.map((slug, i) => [
        slug,
        { slug, color: hues[i % hues.length], weight: 0 },
      ]),
    );
  const pairs = [...data.pairs]
    .filter((p) => p.shared > 0)
    .sort((a, b) => a.shared - b.shared);
  for (const p of pairs) {
    sectors.get(p.a).weight += p.shared;
    sectors.get(p.b).weight += p.shared;
  }
  const total = pairs.reduce((n, p) => n + 2 * p.shared, 0);
  const unit = total ? (2 * Math.PI - keys.length * gap) / total : 0;
  let angle = -Math.PI / 2;
  for (const s of sectors.values()) {
    s.start = s.cursor = angle;
    s.end = angle + s.weight * unit;
    s.mid = (angle + s.end) / 2;
    angle = s.end + gap;
  }
  function arc(r, a, b) {
    return (
      "A " + r + " " + r + " 0 " + Number(b - a > Math.PI) + " 1 " + point(b, r)
    );
  }
  function port(slug, span) {
    const s = sectors.get(slug),
      start = s.cursor;
    s.cursor += span;
    return [start, s.cursor];
  }
  for (const [i, p] of pairs.entries()) {
    const [a, b] = port(p.a, p.shared * unit),
      [f, g] = port(p.b, p.shared * unit);
    const [x1, y1] = point(a, radius),
      [x2, y2] = point(f, radius);
    const grad = svgNode("linearGradient", {
      id: "blend-" + i,
      gradientUnits: "userSpaceOnUse",
      x1,
      y1,
      x2,
      y2,
    });
    for (const [offset, slug] of [
      [0, p.a],
      [1, p.b],
    ])
      grad.append(
        svgNode("stop", { offset, "stop-color": sectors.get(slug).color }),
      );
    defs.append(grad);
    const path = svgNode("path", {
      id: "band-" + i,
      "data-pair": i,
      d:
        "M " +
        point(a, radius) +
        " " +
        arc(radius, a, b) +
        " Q0 0 " +
        point(f, radius) +
        " " +
        arc(radius, f, g) +
        " Q0 0 " +
        point(a, radius) +
        " Z",
      fill: "url(#blend-" + i + ")",
    });
    path.style.opacity = 0.1 + 0.75 * Math.sqrt(p.shared / pairs.at(-1).shared);
    bands.append(path);
  }
  const badges = [];
  for (const s of [...sectors.values()].sort((a, b) => b.weight - a.weight)) {
    const group = svgNode("g", { "data-slug": s.slug });
    const shape =
      "M " + point(s.start, radius + 8) + " " + arc(radius + 8, s.start, s.end);
    group.append(
      svgNode("path", {
        d: shape,
        fill: "none",
        stroke: "transparent",
        "stroke-width": 24,
      }),
      svgNode("path", {
        d: shape,
        fill: "none",
        stroke: s.color,
        "stroke-width": 8,
      }),
    );
    const [cx, cy] = point(s.mid, 263);
    if (
      data.portraits[s.slug] &&
      badges.every(([x, y]) => Math.hypot(cx - x, cy - y) > 56)
    ) {
      badges.push([cx, cy]);
      const id = "portrait-" + s.slug,
        clip = svgNode("clipPath", { id });
      clip.append(svgNode("circle", { cx, cy, r: 19 }));
      defs.append(clip);
      group.append(
        svgNode("path", {
          d: "M " + point(s.mid, radius + 15) + " L " + point(s.mid, 244),
          stroke: s.color,
        }),
        svgNode("circle", { cx, cy, r: 21, fill: s.color }),
        svgNode("image", {
          href: data.portraits[s.slug],
          x: cx - 19,
          y: cy - 19,
          width: 38,
          height: 38,
          "clip-path": "url(#" + id + ")",
        }),
      );
    }
    rim.append(group);
  }
  let pinned = null,
    hover = null,
    last = null,
    pointer = null;
  const touchLayout = matchMedia("(hover: none) and (pointer: coarse)");
  const slot = el("touch-detail"),
    clear = el("clear-pin");
  function placeCard() {
    slot.hidden = !touchLayout.matches;
    (touchLayout.matches ? slot : chart.parentElement).append(card);
    last = undefined;
    refresh();
  }
  const bestFor = (slug) => pairs.findLast((p) => p.a === slug || p.b === slug);
  function target(event) {
    const element = document
      .elementFromPoint(event.clientX, event.clientY)
      ?.closest("[data-pair],[data-slug]");
    if (!element) return null;
    return element.dataset.slug || pairs[Number(element.dataset.pair)];
  }
  function position() {
    if (card.hidden || touchLayout.matches) return;
    const box = chart.getBoundingClientRect(),
      pad = 6;
    const x = pointer ? pointer.x - box.left : box.width * 0.5,
      y = pointer ? pointer.y - box.top : box.height * 0.56;
    const w = card.offsetWidth,
      h = card.offsetHeight;
    // Clamp continuously at the edges; flipping sides makes the card jump a full card width.
    const left = Math.max(pad, Math.min(box.width - w - pad, x + 16));
    const top = Math.max(pad, Math.min(box.height - h - pad, y + 16));
    card.style.transform = `translate3d(${left}px, ${top}px, 0)`;
  }
  function person(slug, share) {
    const row = node("div");
    row.className = "portrait-line";
    if (data.portraits[slug]) {
      const image = node("img");
      image.src = data.portraits[slug];
      image.alt = "";
      row.append(image);
    }
    const caption = node("div");
    caption.append(
      node("strong", names[slug]),
      node("small", share + "% of holders"),
    );
    row.append(caption);
    return row;
  }
  function refresh() {
    const focus = hover || pinned || filter.value || null;
    if (focus !== last) {
      const slug = typeof focus === "string" ? focus : null,
        pair = slug
          ? bestFor(slug)
          : focus || (touchLayout.matches ? pairs.at(-1) : null);
      overlay.replaceChildren();
      chart.classList.toggle("inspecting", !!focus);
      for (const g of rim.children)
        g.classList.toggle(
          "lit",
          g.dataset.slug === slug ||
            (!!pair && [pair.a, pair.b].includes(g.dataset.slug)),
        );
      if (focus) {
        pairs.forEach((p, i) => {
          if (p === pair || (slug && (p.a === slug || p.b === slug)))
            overlay.append(
              svgNode("path", {
                d: bands.children[i].getAttribute("d"),
                fill: "url(#blend-" + i + ")",
                stroke: p === pair ? "#f6e6ff" : "none",
                "stroke-width": 0.85,
                opacity: p === pair ? 1 : 0.55,
              }),
            );
        });
      }
      clear.hidden = !touchLayout.matches || !focus;
      card.hidden = !pair;
      card.replaceChildren();
      if (pair) {
        const label = node(
          "small",
          !focus
            ? "Largest overlap"
            : slug
              ? "Closest neighbor"
              : "Shared addresses",
        );
        const count = node("b", fmt(pair.shared));
        card.append(
          label,
          count,
          person(pair.a, pair.pct_a),
          person(pair.b, pair.pct_b),
        );
        el("readout").textContent = !focus
          ? "Tap a collection or ribbon to inspect its shared holders."
          : names[pair.a] +
            " × " +
            names[pair.b] +
            " · " +
            fmt(pair.shared) +
            " shared addresses.";
      } else {
        el("readout").textContent =
          "Hover or tap a ribbon to compare two collections.";
      }
      last = focus;
    }
    const lead = pinned || filter.value || pairs.at(-1);
    el("map-link").href = studyURL(
      "overlap",
      typeof lead === "string" ? lead : lead?.a,
    );
    position();
  }
  let pending, timer, frame;
  function cancelHover() {
    clearTimeout(timer);
    cancelAnimationFrame(frame);
    pending = undefined;
    frame = 0;
  }
  function consider(next) {
    if (next === pending) return;
    clearTimeout(timer);
    pending = next;
    if (next === hover) return;
    if (next && card.hidden) {
      hover = next;
      refresh();
      return;
    }
    timer = setTimeout(
      () => {
        hover = next;
        if (!next && !pinned) pointer = null;
        refresh();
      },
      next ? 95 : 140,
    );
  }
  function reset() {
    cancelHover();
    pinned = hover = pointer = null;
    filter.value = "";
    refresh();
  }
  filter.onchange = () => {
    cancelHover();
    pinned = hover = pointer = null;
    refresh();
  };
  chart.onpointermove = (e) => {
    if (pinned || e.pointerType === "touch") return;
    pointer = { x: e.clientX, y: e.clientY };
    if (!frame)
      frame = requestAnimationFrame(() => {
        frame = 0;
        consider(target({ clientX: pointer.x, clientY: pointer.y }));
        position();
      });
  };
  chart.onpointerleave = () => {
    if (pinned) return;
    cancelAnimationFrame(frame);
    frame = 0;
    consider(null);
  };
  chart.onclick = (e) => {
    cancelHover();
    const hit = target(e);
    if (!hit || hit === pinned) {
      reset();
      return;
    }
    pinned = hit;
    hover = null;
    filter.value = typeof hit === "string" ? hit : "";
    pointer = { x: e.clientX, y: e.clientY };
    refresh();
  };
  chart.onkeydown = (e) => {
    if (!["ArrowLeft", "ArrowRight", "Escape"].includes(e.key)) return;
    e.preventDefault();
    cancelHover();
    if (e.key === "Escape") {
      reset();
      return;
    }
    const candidates = pairs
      .filter(
        (p) => !filter.value || p.a === filter.value || p.b === filter.value,
      )
      .reverse();
    if (!candidates.length) return;
    const index = candidates.indexOf(pinned);
    pinned =
      candidates[
        index < 0
          ? 0
          : (index + (e.key === "ArrowRight" ? 1 : -1) + candidates.length) %
            candidates.length
      ];
    hover = pointer = null;
    refresh();
  };
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !el("home").hidden) reset();
  });
  new ResizeObserver(position).observe(chart);
  clear.onclick = reset;
  touchLayout.addEventListener("change", placeCard);
  drawAtlas = refresh;
  placeCard();
}
