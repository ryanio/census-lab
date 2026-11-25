// Compare identical category/value pairs across collections. Count each collection once.
function initSharedTraits() {
  const groups = new Map();
  const normalize = (text) => text.trim().toLowerCase();
  const examples = new Map();
  for (const [slug, tokens] of Object.entries(data.traitExamples)) {
    for (const token of tokens) {
      for (const [category, value] of token.traits) {
        const key = JSON.stringify([slug, category, value]);
        if (!examples.has(key)) examples.set(key, []);
        examples.get(key).push(token);
      }
    }
  }
  for (const [slug, categories] of Object.entries(data.traits)) {
    for (const [category, values] of Object.entries(categories)) {
      for (const [label, count] of values) {
        const key = JSON.stringify([normalize(category), normalize(label)]);
        if (!groups.has(key)) groups.set(key, {category, label, members: new Map()});
        const members = groups.get(key).members;
        // Case variants may describe the same NFTs. Keep their reported counts separate.
        if (!members.has(slug)) members.set(slug, []);
        members.get(slug).push(count);
      }
    }
  }
  const shared = [...groups.values()].filter(g => g.members.size > 1).sort((a,b) =>
    b.members.size - a.members.size || a.label.localeCompare(b.label));
  const picker = el("shared-label"), family = el("shared-category"), wall = el("trait-wall");
  if (!shared.length) { el("shared-study").hidden = true; return; }
  const families = [...new Set(shared.map(g => normalize(g.category)))].sort();
  family.replaceChildren(...families.map(c => new Option(c, c)));
  const shortcuts = new Map();
  let choices = [], expanded = false;
  const lineup = new Map();
  function pool(group, slug) {
    return examples.get(JSON.stringify([slug, normalize(group.category), normalize(group.label)])) || [];
  }
  function draw() {
    const group = choices[picker.selectedIndex];
    el("lineup-status").replaceChildren();
    for (const [trait, button] of shortcuts) {
      button.setAttribute("aria-pressed", String(trait === group));
    }
    const members = [...group.members].sort(([a],[b]) => names[a].toLowerCase() < names[b].toLowerCase() ? -1 : names[a].toLowerCase() > names[b].toLowerCase() ? 1 : a.localeCompare(b));
    el("shared-head").textContent = group.label + " in " + members.length + " collections";
    const comparable = members.filter(([, counts]) => counts.length === 1)
      .sort((a, b) => b[1][0] - a[1][0]);
    const first = comparable[0], last = comparable.at(-1);
    el("shared-finding").textContent = comparable.length > 1 && first[1][0] !== last[1][0]
      ? names[first[0]] + " reports " + fmt(first[1][0]) + " NFTs with this label. " +
        names[last[0]] + " reports " + fmt(last[1][0]) + ". These counts reflect collection size as well as trait frequency."
      : "";
    wall.replaceChildren();
    for (const [slug, counts] of expanded ? members : members.slice(0,6)) {
      const example = lineup.get(slug);
      const tile = node("figure"), caption = node("figcaption");
      if (example) {
        const tokenName = names[slug] + " #" + example.token;
        const asset = link("", example.url), img = node("img");
        img.alt = tokenName + " (" + group.category + ": " + group.label + ")";
        img.loading = "lazy";
        img.onerror = () => asset.replaceChildren(node("span", "View artwork on OpenSea"));
        img.src = Object.keys(data.lineupCards).length && /\.(mp4|webm)(\?|$)/i.test(example.image)
          ? new URL("stills/" + slug + "/" + example.token + ".webp", editionURL("traits")).href
          : example.image;
        asset.append(img);
        tile.append(asset);
        caption.append(node("strong", names[slug]), link("#" + example.token, example.url));
      } else {
        caption.append(node("strong", names[slug]), node("small", "Example unavailable"));
      }
      caption.append(node("span", counts.map(fmt).join(" / ") + " NFTs"));
      tile.append(caption); wall.append(tile);
    }
    const more = el("shared-more");
    more.hidden = members.length <= 6;
    more.textContent = expanded ? "Show first six" : "Show all " + members.length + " collections";
    more.setAttribute("aria-expanded", String(expanded));
  }
  function selectGroup(group, saved = null) {
    const category = normalize(group.category);
    if (!choices.includes(group)) {
      family.value = category;
      choices = shared.filter(g => normalize(g.category) === category);
      picker.replaceChildren(...choices.map(g => new Option(g.label + " (" + g.members.size + ")")));
      el("trait-prev").disabled = el("trait-next").disabled = choices.length < 2;
    }
    picker.selectedIndex = choices.indexOf(group);
    lineup.clear();
    let canShuffle = false;
    for (const [i, slug] of [...group.members.keys()].sort().entries()) {
      const tokens = pool(group, slug);
      const selected = saved && tokens.find(t => t.token === saved[i]);
      lineup.set(slug, selected || tokens[0]);
      canShuffle ||= tokens.length > 1;
    }
    el("shuffle-pfps").disabled = !canShuffle;
    expanded = false;
    draw();
  }
  function browse(group) {
    selectGroup(group);
    explore("traits", "browse_trait");
  }
  for (const [category, label] of [["mouth", "tongue out"], ["eyes", "3d glasses"], ["head", "halo"]]) {
    const pick = groups.get(JSON.stringify([category, label]));
    if (!pick || pick.members.size < 2) continue;
    const button = node("button", pick.label);
    button.type = "button";
    button.onclick = () => browse(pick);
    shortcuts.set(pick, button);
    el("trait-shuffle").before(button);
  }
  function step(offset) {
    browse(choices[(picker.selectedIndex + offset + choices.length) % choices.length]);
  }
  el("trait-prev").onclick = () => step(-1);
  el("trait-next").onclick = () => step(1);
  el("trait-shuffle").disabled = shared.length < 2;
  el("trait-shuffle").onclick = () => {
    const current = shared.indexOf(choices[picker.selectedIndex]);
    const offset = 1 + Math.floor(Math.random() * (shared.length - 1));
    browse(shared[(current + offset) % shared.length]);
  };
  family.onchange = () => browse(shared.find(g => normalize(g.category) === family.value));
  picker.onchange = () => browse(choices[picker.selectedIndex]);
  el("shared-more").onclick = () => { expanded = !expanded; draw(); };
  el("shuffle-pfps").onclick = () => {
    const group = choices[picker.selectedIndex];
    const card = data.lineupCards[JSON.stringify([normalize(group.category), normalize(group.label)])];
    if (card) {
      const score = round => round.ids.reduce((n, id, i) => n + (id !== lineup.get(card.slugs[i])?.token), 0);
      const best = Math.max(...card.rounds.map(score));
      const choices = card.rounds.filter(round => score(round) === best);
      const next = choices[Math.floor(Math.random() * choices.length)];
      const wasExpanded = expanded;
      selectGroup(group, next.ids);
      expanded = wasExpanded;
    } else {
      for (const [slug, current] of lineup) {
        const others = pool(group, slug).filter(token => token !== current);
        if (others.length) lineup.set(slug, others[Math.floor(Math.random() * others.length)]);
      }
    }
    draw();
    el("lineup-status").textContent = "PFPs shuffled";
    explore("traits", "shuffle_lineup");
  };
  el("save-lineup").onclick = async () => {
    const save = el("save-lineup");
    save.disabled = true;
    const group = choices[picker.selectedIndex];
    const visible = [...wall.querySelectorAll("figure")];
    try {
      const tiles = await Promise.all(visible.map(async figure => {
        const source = figure.querySelector("img");
        if (!source) throw new Error("Missing artwork");
        const image = new Image();
        image.crossOrigin = "anonymous";
        image.src = source.src;
        await image.decode();
        return {image, name: figure.querySelector("strong").textContent, token: figure.querySelector("figcaption a").textContent};
      }));
      const canvas = node("canvas"), columns = Math.min(3, tiles.length);
      const side = 300, gap = 20, margin = 36, rowHeight = 380;
      canvas.width = 2 * margin + columns * side + (columns - 1) * gap;
      canvas.height = 174 + Math.ceil(tiles.length / columns) * rowHeight;
      const ctx = canvas.getContext("2d");
      ctx.fillStyle = "#f4e6d7";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = "#412b20";
      ctx.font = "20px monospace";
      ctx.fillText("Census  /  " + group.category, margin, 40);
      ctx.font = "56px Georgia";
      ctx.fillText(group.label, margin, 108, canvas.width - margin * 2);
      tiles.forEach(({image, name, token}, i) => {
        const x = margin + (i % columns) * (side + gap), y = 138 + Math.floor(i / columns) * rowHeight;
        const scale = side / Math.max(image.width, image.height);
        const w = image.width * scale, h = image.height * scale;
        ctx.drawImage(image, x + (side - w) / 2, y + (side - h) / 2, w, h);
        ctx.font = "bold 22px sans-serif";
        ctx.fillText(name, x, y + side + 29, side);
        ctx.font = "18px monospace";
        ctx.fillText(token, x, y + side + 54, side);
      });
      ctx.font = "17px monospace";
      ctx.fillText("ryanio.github.io/census-lab  /  " + data.edition, margin, canvas.height - 20, canvas.width - margin * 2);
      const url = canvas.toDataURL("image/png");
      const download = link("", url);
      download.download = "census-" + group.label.toLowerCase().replace(/[^a-z0-9]+/g, "-") + ".png";
      download.click();
    } catch {
      el("lineup-status").textContent = "Artwork could not be exported. You can still copy the lineup link.";
    } finally {
      save.disabled = false;
    }
  };
  el("share-lineup").onclick = () => {
    const group = choices[picker.selectedIndex];
    const url = editionURL("traits");
    url.searchParams.set("category", normalize(group.category));
    url.searchParams.set("trait", normalize(group.label));
    url.searchParams.set("tokens", [...lineup.keys()].sort().map(slug => lineup.get(slug)?.token || "").join("."));
    if (expanded) url.searchParams.set("all", "1");

    const card = data.lineupCards[JSON.stringify([normalize(group.category), normalize(group.label)])];
    const matching = card?.rounds.find(round => round.ids.every((id, i) => id === lineup.get(card.slugs[i])?.token));
    const preview = matching && new URL("lineups/" + matching.path + (expanded && card.slugs.length > 6 ? "/all/" : "/"), url);
    copyStudyLink(preview || url, el("lineup-status"), "traits");
  };
  const query = new URLSearchParams(location.search);
  const requested = groups.get(JSON.stringify([query.get("category"), query.get("trait")]));
  if (requested && requested.members.size > 1) {
    selectGroup(requested, (query.get("tokens") || "").split("."));
    expanded = query.get("all") === "1";
    draw();
  } else selectGroup(shortcuts.keys().next().value || shared.find(g => normalize(g.category) !== "background") || shared[0]);
}
