// Compare identical category/value pairs across collections. Count each collection once.
function initSharedTraits() {
  const groups = new Map();
  const normalize = (text) => text.trim().toLowerCase();
  const examples = new Map(data.colors.filter((r) => r.image && r.url).map((r) =>
    [JSON.stringify([r.slug, normalize(r.category), normalize(r.value)]), r]));
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
  function draw() {
    const group = choices[picker.selectedIndex];
    for (const [trait, button] of shortcuts) {
      button.setAttribute("aria-pressed", String(trait === group));
    }
    const members = [...group.members].sort(([a],[b]) => names[a].localeCompare(names[b]));
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
      const example = examples.get(JSON.stringify([slug, normalize(group.category), normalize(group.label)]));
      const tile = node("figure"), caption = node("figcaption"), img = node("img");
      img.alt = ""; img.loading = "lazy";
      if (example) {
        const asset = link("", example.url);
        asset.setAttribute("aria-label", "View " + names[slug] + " example on OpenSea");
        img.src = example.image;
        asset.append(img); tile.append(asset);
      } else if (data.portraits[slug]) {
        img.src = data.portraits[slug]; tile.append(img);
      }
      caption.append(node("strong", names[slug]), node("span", counts.map(fmt).join(" / ") + " NFTs"),
        node("small", example ? "Trait example" : "Collection portrait"));
      tile.append(caption); wall.append(tile);
    }
    const more = el("shared-more");
    more.hidden = members.length <= 6;
    more.textContent = expanded ? "Show first six" : "Show all " + members.length + " collections";
    more.setAttribute("aria-expanded", String(expanded));
  }
  function selectGroup(group) {
    const category = normalize(group.category);
    if (!choices.includes(group)) {
      family.value = category;
      choices = shared.filter(g => normalize(g.category) === category);
      picker.replaceChildren(...choices.map(g => new Option(g.label + " (" + g.members.size + ")")));
      el("trait-prev").disabled = el("trait-next").disabled = choices.length < 2;
    }
    picker.selectedIndex = choices.indexOf(group);
    expanded = false;
    draw();
  }
  for (const [category, label] of [["mouth", "tongue out"], ["eyes", "3d glasses"], ["head", "halo"]]) {
    const pick = groups.get(JSON.stringify([category, label]));
    if (!pick || pick.members.size < 2) continue;
    const button = node("button", pick.label);
    button.type = "button";
    button.onclick = () => selectGroup(pick);
    shortcuts.set(pick, button);
    el("trait-shuffle").before(button);
  }
  function step(offset) {
    selectGroup(choices[(picker.selectedIndex + offset + choices.length) % choices.length]);
  }
  el("trait-prev").onclick = () => step(-1);
  el("trait-next").onclick = () => step(1);
  el("trait-shuffle").disabled = shared.length < 2;
  el("trait-shuffle").onclick = () => {
    const current = shared.indexOf(choices[picker.selectedIndex]);
    const offset = 1 + Math.floor(Math.random() * (shared.length - 1));
    selectGroup(shared[(current + offset) % shared.length]);
  };
  family.onchange = () => selectGroup(shared.find(g => normalize(g.category) === family.value));
  picker.onchange = () => selectGroup(choices[picker.selectedIndex]);
  el("shared-more").onclick = () => { expanded = !expanded; draw(); };
  selectGroup(shortcuts.keys().next().value || shared.find(g => normalize(g.category) !== "background") || shared[0]);
}
