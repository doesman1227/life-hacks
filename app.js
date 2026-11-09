// パーソナルデータベースのページ共通のスクリプト。index・picks・want の三枚が読む。
// items.json を一度読んで、そのページにある描き込み先だけを埋める。
// 経験・体験／モノ／場所・旅行の三セクションで、このファイルの中身は同一。
// 違いはすべて items.json 側（build_items.py）に持たせてあるので、ここを分岐させない。
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

// アイコンは各HTMLに埋め込んである線画を使う。知らない名前が来たら星にしておく。
const icon = (name, cls = "") => `<svg class="ic ${cls}" aria-hidden="true"><use href="#ic-${esc(name || "star")}"/></svg>`;

// 題名は公式ページへ送る。リンクの無いものは文字のまま。
const titleLink = it => it.url
  ? `<a class="kb" href="${esc(it.url)}" target="_blank" rel="noopener">${esc(it.title)}</a>`
  : esc(it.title);

// 細目は index の領域別へ送る。三枚を行き来できるようにしておく。
const subTag = (it, home) => it.sub
  ? `<a class="gl" href="${home}#genre">${esc(it.sub)}</a>` : "";

// 手元の記録（つぶやきや別のノート）への相対リンク。
const srcLink = it => it.source
  ? `<a class="gl" href="${esc(it.source)}">元になった記録 →</a>` : "";

// picks と want のカード。年を持つのは過去の行だけなので、無ければ出さない。
// 写真があるものは、アイコンのかわりに写真を出す。
// 写真の有無は build_items.py が images/<slug>.jpg を見て決めている。
const badge = (it, useIcon) => it.img
  ? `<span class="badge shot"><img src="${esc(it.img)}" alt="" loading="lazy"></span>`
  : `<span class="badge">${icon(useIcon)}</span>`;

function card(it, useIcon, home) {
  const meta = subTag(it, home)
    + (it.year ? `<span>${esc(it.year)}年</span>` : "")
    + srcLink(it);
  return `<div class="pick">
    <div class="hd">
      ${badge(it, useIcon)}
      <span class="ttl"><b>${titleLink(it)}</b>
        ${it.note ? `<span class="what">${esc(it.note)}</span>` : ""}
      </span>
    </div>
    ${it.memo ? `<p class="memo">${esc(it.memo)}</p>` : ""}
    <div class="meta">${meta}</div>
  </div>`;
}

// picks と want は領域ごとの節に分ける。節の順番は領域の並びのまま。空の節は出さない。
// 領域に入れていないものは、黙って消さずに最後の節へまとめる。
function useGroups(list, uses, home) {
  const groups = uses.map(u => [u, list.filter(x => x.use === u.name)]);
  const rest = list.filter(x => !x.use);
  if (rest.length) groups.push([{name: "そのほか", icon: "star", subs: []}, rest]);
  return groups.map(([u, got]) => {
    if (!got.length) return "";
    const head = u.ref
      ? `<a class="kb" href="${esc(u.ref)}">${esc(u.name)}</a>` : esc(u.name);
    return `<div class="cg">
      <div class="cgh">
        <span class="badge">${icon(u.icon)}</span>
        <h3>${head}</h3>
        <span class="n">${got.length}件</span>
      </div>
      <div class="picks">${got.map(x => card(x, u.icon, home)).join("")}</div>
    </div>`;
  }).join("");
}

// 領域別の一枚。細目ごとに題名を並べる。まだ何も無い領域はそう書く。
function useCard(u, list, wanted) {
  const rows = (u.subs || []).map(name => {
    const got = list.filter(it => it.sub === name);
    if (!got.length) return "";
    const names = got.map(it => `<span class="un">${titleLink(it)}</span>`).join("");
    return `<div class="sub"><dt>${esc(name)}</dt><dd>${names}</dd></div>`;
  }).join("");
  const n = list.length ? `${list.length}件` : "";
  const wn = wanted ? `<span class="wn${n ? "" : " solo"}">これから${wanted}</span>` : "";
  const name = u.ref
    ? `<a class="kb" href="${esc(u.ref)}">${esc(u.name)}</a>` : esc(u.name);
  return `<div class="use">
    <div class="uh">
      <span class="badge">${icon(u.icon)}</span>
      <span class="ut"><b>${name}</b><span class="uen">${esc(u.en)}</span></span>
      <span class="n">${n}${wn}</span>
    </div>
    ${rows ? `<dl class="subs">${rows}</dl>` : `<p class="none">まだありません。</p>`}
  </div>`;
}

// 年別の帯。優待の「届く月」と同じ形。年を持たないものは最後の「時期不明」へ。
function yearBlock(label, list, max) {
  const w = list.length ? Math.max(4, Math.round(list.length / max * 100)) : 0;
  const items = list.map(it => `<li><span>${titleLink(it)}</span>${
    it.note ? `<span class="w">${esc(it.note)}</span>` : ""}</li>`).join("");
  return `<div class="month${list.length ? "" : " none"}">
    <div class="mh">
      <span class="mn">${esc(label)}</span>
      <span class="track"><span class="bar" style="width:${w}%"></span>
        <span class="mc">${list.length ? list.length + "件" : "なし"}</span></span>
    </div>
    ${list.length ? `<ul>${items}</ul>` : ""}
  </div>`;
}

function render(data) {
  const items = data.items || [];
  const wants = data.wants || [];
  const uses = data.uses || [];
  const byTitle = (a, b) => a.title.localeCompare(b.title, "ja");

  // お気に入りのレーン。メモを持つものだけが出る。新しい年のものから。
  const picks = items.filter(it => it.memo)
    .sort((a, b) => (b.year || "0").localeCompare(a.year || "0") || byTitle(a, b));
  const pickBox = document.querySelector("[data-picks]");
  if (pickBox) pickBox.innerHTML = picks.length ? useGroups(picks, uses, "./")
    : `<p class="empty">まだありません。</p>`;

  // これからのレーン。いま進めているものを先頭の節に分ける。
  const wantBox = document.querySelector("[data-wants]");
  if (wantBox) {
    const now = wants.filter(w => w.state === "いま");
    const ahead = wants.filter(w => w.state !== "いま");
    const nowBlock = now.length ? `<div class="cg">
      <div class="cgh">
        <span class="badge">${icon("sparkle")}</span>
        <h3>いま進めていること</h3>
        <span class="n">${now.length}件</span>
      </div>
      <div class="picks">${now.map(w => card(w, "sparkle", "./")).join("")}</div>
    </div>` : "";
    wantBox.innerHTML = wants.length ? nowBlock + useGroups(ahead, uses, "./")
      : `<p class="empty">まだありません。</p>`;
  }

  // 領域別
  const placed = items.filter(it => it.use);
  const useBox = document.querySelector("[data-uses]");
  if (useBox) useBox.innerHTML = uses.length
    ? uses.map(u => useCard(u, placed.filter(it => it.use === u.name).sort(byTitle),
        wants.filter(w => w.use === u.name).length)).join("")
    : `<p class="empty">まだありません。</p>`;

  // 領域に入れていないものがどこへ行ったのかは、黙って消すより書いておく
  const leftBox = document.querySelector("[data-left]");
  if (leftBox) leftBox.textContent = data.left || "";

  // 年別。一件も年を持たないときは、空の帯が並ぶだけなので節ごと出さない。
  const yearBox = document.querySelector("[data-years]");
  if (yearBox) {
    const years = [...new Set(items.map(it => it.year).filter(Boolean))].sort().reverse();
    if (!years.length) {
      yearBox.closest("section")?.remove();
      document.querySelector('.toc a[href="#years"]')?.closest("li")?.remove();
    } else {
      const unknown = items.filter(it => !it.year).sort(byTitle);
      const rows = years.map(y => [y + "年", items.filter(it => it.year === y).sort(byTitle)]);
      if (unknown.length) rows.push(["時期不明", unknown]);
      const max = Math.max(1, ...rows.map(([, l]) => l.length));
      yearBox.innerHTML = rows.map(([label, l]) => yearBlock(label, l, max)).join("");
    }
  }

  document.querySelectorAll("[data-count]").forEach(el => {
    const k = el.dataset.count;
    const n = k === "picks" ? picks.length
      : k === "wants" ? wants.length
      : k === "uses" ? placed.length : items.length;
    el.textContent = n ? n + "件" : "";
  });
}

// 目次から注意書きへ飛んだときは、畳んだままだと何も見えないので開く。
const openCaution = () => {
  if (location.hash === "#caution") {
    const d = document.querySelector("#caution details");
    if (d) d.open = true;
  }
};
addEventListener("hashchange", openCaution);
openCaution();

// 一度来た人のブラウザには古い items.json が残っている。ページだけ新しくなると
// 形が噛み合わず全部が読み込み失敗になるので、毎回サーバーに確かめさせる。
fetch("items.json", {cache: "no-cache"}).then(r => r.json()).then(render).catch(() => {
  document.querySelectorAll("[data-picks],[data-wants],[data-uses],[data-years]").forEach(
    el => el.innerHTML = `<p class="empty">データを読み込めませんでした。</p>`);
});
