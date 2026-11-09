#!/usr/bin/env python3
"""経験の記録から items.json を書き出す。パーソナルデータベースの三大分類のひとつ。

やったこと（ROWS）・やって良かったこと（PICKS）・やりたいこと（WANTS）の三レーン。
事実と評価を分けてあるのがこの形の肝で、やったことは ROWS に一度だけ書き、
やって良かった理由は PICKS に別で持つ。PICKS に載せた分だけ picks.html に出る。

世の中で言われているライフハックの候補は catalog.html にある。あちらは他人の工夫の一覧で、
こちらは自分が実際にやったことの記録。混ぜない。候補から試したくなったものを
WANTS に書き、実際にやったら ROWS へ移す、という流れを想定している。
領域の名前は catalog.html と同じ16語にしてあるので、領域の見出しから候補の節へ飛べる。

★このファイルは公開リポジトリに入り、誰でも全文を読める。非公開という状態は
持たない方針なので、公開していいものだけを書く。仕事のこと、体調や通院の細かいところ、
人の名前は書かない。日付も月までにして、日付までは書かない。

直し方は二通り。手元で直して python3 build_items.py を走らせるか、GitHub の編集画面で
このファイルだけを直してコミットするか。後者の場合は .github/workflows/build.yml が
代わりに走らせて items.json を作り直すので、手元のパソコンは要らない。どちらの場合も、
手元で続きを直すときは先に git pull しておく（向こうのコミットが増えているため）。
"""

import hashlib
import json
import re
from pathlib import Path

NOTE = ("経験・体験（やったこと・やって良かったこと・やりたいこと）。"
        "build_items.py が書き出す。直すのはあちら。")

# やったこと。区切りは | で、順番は
# slug | 題名 | 年 | 一行 | リンク | 元になった記録
# 年はやった年。分からないものは空にしておく（「時期不明」に入る）。
ROWS = """
m-note|頭の中を、ホームページにした|2026|考えていること、興味のあること、世界の捉え方を見える形に。それがこの m-note になった。||../about/
slow-run|会話できる速さで走りはじめた|2026|追い込まず、苦しくなったら歩く。長く動き続ける感覚を育てる。||../musings/posts/p051.html
sauna|サウナと外気浴で、ほどける|2026|||../musings/posts/p082.html
"""

# やって良かったこと。ここに載せた分だけ picks.html に出る。
# 文は self.json の「楽しかったこと」からそのまま移した。
PICKS = {
    "sauna": "背筋が伸びて、頭が少し真っ白になる感じ。体が「もう緊張を解いていい」と感じる時間。",
}

# やりたいこと。区切りは | で、順番は
# slug | 題名 | 一行 | メモ | 領域 | 細目 | 状態 | リンク | 元になった記録
# 領域は下の USES の領域名から選ぶ（違う語はビルドで止まる）。細目は自由語でよい。
# 状態に「いま」と書くと、want.html の先頭の節に入る。空なら「これから」。
# 「いま」のものは、一行にいつからいつまでを書いておく。
WANTS = """
closet-cleanup|クローゼットと靴箱を片付ける|2026.10 中旬〜|部屋を片付ける、最初の一か所。服と靴を全部出して、「残す・手放す・迷う」に分ける。気持ちが上がらないものは、手放す候補に。|住む|片付け|いま||
suit-shoes|スーツと靴を整える|〜2026.11 中旬|片付けのあとに、手入れ・買い替え・追加を3つ以内のリストにして、1つ目を実行する。最初に買うのは靴から。スーツは、いまあるものを直すことを先に、新しく買うのは体が整ってから。|着る|手入れ|いま||
tidy-room|部屋を片付けて、物を減らす||必要なものと、好きなもの。素敵なものだけに囲まれて暮らしたい。|住む|片付け|||
move|心地よい場所に引っ越す||適度に広く、心地よい住まいへ。今の家も気に入っているから、公園と自然、ジムの近さはそのままに。|住む|住まい|||../musings/posts/p072.html
good-food|おいしいものを食べる||日常を豊かにする、いちばん身近な楽しみ。|食べる|外食|||../food/
meet-people|いろいろな人と関わる||人と話して、新しい考え方に触れたい。|人づきあい|人と話す|||
yutai-best|株主優待の最適解をまとめる||たくさんある株主優待の中から、自分の暮らしにとっての最適解を整理したい。|おかね|株主優待|||../money/
make-something|何かを作り上げる||何を作りたいのかは、まだ言葉にしている途中。形にしたいものの候補は、下の二つ。|発想|つくる|||../way-of-creating/
ai-architecture|AIで、存在しない建築をつくる||森に建てるのではなく、森から生まれた家。苔と岩と植物が溶け合う建築を、コンセプトから外観・内観・ウォークスルーまで。|発想|つくる|||../musings/posts/p103.html
photo-site|写真を入り口に、記憶をたどるサイトをつくる||何を撮るかより、何を感じるか。建物・自然・人の写真から、記憶や感情がネットワーク状に広がる場所。|発想|つくる|||../musings/posts/p060.html
get-healthy|健康的に痩せて、健康な体になる||ダイエットしたい。でも数字を減らすことより、無理をせず、健康的な体になることを大切にしたい。|体|からだづくり|||../health-habits/
english|英語で考え、話せるようになる||勉強ではなく、英語を使って考えること。毎日少しだけ、AIを相手に話す。|学び|英語|||../musings/posts/p036.html
after-climb|登山のあとの感覚を、もう一度||きつかったのに、いい気持ちだった。あの感覚をくれる活動を、登山以外にも探してみたい。|体|からだづくり|||../musings/posts/p143.html
"""

# 領域と細目。字下げの無い行が領域で 領域名|英字|アイコン|参照先、
# 字下げした行が細目で 細目名|slug,slug。同じものは一つの細目にだけ置く。
# 16の領域名と参照先は catalog.html の節に合わせてある。語をずらさないこと。
USES = """
時間|TIME|clock|catalog.html#time
集中|FOCUS|target|catalog.html#focus
学び|LEARNING|book|catalog.html#learn
発想|IDEAS|bulb|catalog.html#ideas
住む|HOME|home|catalog.html#home
着る|CLOTHES|shirt|catalog.html#clothes
食べる|FOOD|meal|catalog.html#food
体|BODY|pulse|catalog.html#health
  走る|slow-run
  ととのえる|sauna
眠り|SLEEP|bed|catalog.html#sleep
おかね|MONEY|card|catalog.html#money
デジタル|DIGITAL|laptop|catalog.html#digital
旅と持ち物|TRAVEL|bag|catalog.html#travel
気持ち|MOOD|heart|catalog.html#mood
頭の中|MIND|brain|catalog.html#mind
  書いて外に出す|m-note
人づきあい|PEOPLE|people|catalog.html#people
備え|READY|shield|catalog.html#ready
"""

# 領域に入れないもの。いまは無い。
OUT = """
"""

# 領域に出していないものについての一行。出していないものが無ければ空。
LEFT = ""

ASSETS = ["style.css", "app.js"]
PAGES = ["index.html", "picks.html", "want.html"]
SLUG = re.compile(r"^[a-z0-9-]+$")
YEAR = re.compile(r"^[12][0-9]{3}$")
# app.js が領域の外のものと「いま」の節に使うアイコン。どのページにも要る。
ALWAYS = ["star", "sparkle"]


def rows(block, cols):
    """| 区切りの表を読む。列の数が合わない行はその場で止める。"""
    out = []
    for n, line in enumerate(block.strip().splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) != len(cols):
            raise SystemExit(f"{n}行目の列が{len(parts)}個（{len(cols)}個のはず）: {line}")
        out.append(dict(zip(cols, parts)))
    return out


def check_common(it, where):
    """slug・年・リンクの書き方を確かめる。どれも直せば通る形の間違い。"""
    if not SLUG.match(it["slug"]):
        raise SystemExit(f"{where} の slug は英小文字・数字・ハイフンだけ: {it['slug']}")
    if it.get("year") and not YEAR.match(it["year"]):
        raise SystemExit(f"{where} の年は4桁: {it['slug']} の {it['year']}")
    if it.get("url") and not it["url"].startswith(("http://", "https://")):
        raise SystemExit(f"{where} のリンクは http/https だけ: {it['slug']}")
    if it.get("source") and not it["source"].startswith(("./", "../")):
        raise SystemExit(f"{where} の元になった記録は相対パスで: {it['slug']} の {it['source']}")


def check_icons(here, names):
    """使うアイコンが三枚ぜんぶに埋まっているか確かめる。

    優待で一度やられている。want.html にアイコンを三つしか持たせないまま銘柄を足して、
    カードの丸が空のまま公開された。線画は各HTMLに埋め込む作りなので、
    一枚だけ足し忘れても他の二枚では正しく出てしまい、見落としやすい。
    """
    for page in PAGES:
        have = set(re.findall(r'<symbol id="ic-([a-z0-9-]+)"', (here / page).read_text(encoding="utf-8")))
        missing = sorted(set(names) - have)
        if missing:
            raise SystemExit(f"{page} にアイコンが埋まっていない: {missing}")


def stamp_assets(here):
    """style.css と app.js の URL に中身のハッシュを付ける。

    一度来た人のブラウザには前の app.js が残っている。ページとデータだけ新しくなると
    古いコードが新しい形の items.json を読むことになり、節がまるごと出なくなる。
    中身が変わればURLも変わるようにして、取り違えが起きないようにする。
    """
    tag = hashlib.sha256(b"".join((here / f).read_bytes() for f in ASSETS)).hexdigest()[:8]
    touched = []
    for page in here.glob("*.html"):
        t = u = page.read_text(encoding="utf-8")
        for f in ASSETS:
            u = re.sub(rf'({re.escape(f)})(\?v=[0-9a-f]+)?"', rf'\1?v={tag}"', u)
        if u != t:
            page.write_text(u, encoding="utf-8")
            touched.append(page.name)
    return f"共通ファイルの版を {tag} にした" + (f"（{'・'.join(touched)}）" if touched else "（変更なし）")


def main():
    items = rows(ROWS, ["slug", "title", "year", "note", "url", "source"])
    wants = rows(WANTS, ["slug", "title", "note", "memo", "use", "sub", "state", "url", "source"])

    for it in items:
        check_common(it, "ROWS")
    for w in wants:
        check_common(w, "WANTS")

    slugs = [i["slug"] for i in items] + [w["slug"] for w in wants]
    dup = sorted({s for s in slugs if slugs.count(s) > 1})
    if dup:
        raise SystemExit(f"slug が重なっている: {dup}")

    by_slug = {i["slug"]: i for i in items}
    unknown = sorted(set(PICKS) - set(by_slug))
    if unknown:
        raise SystemExit(f"PICKS に ROWS に無い slug がある: {unknown}")
    for slug, memo in PICKS.items():
        by_slug[slug]["memo"] = memo

    # 領域と細目。字下げの無い行が領域、字下げした行が細目。
    uses, seen = [], []
    for line in USES.strip().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  "):
            if not uses:
                raise SystemExit(f"領域より先に細目が来ている: {line.strip()}")
            sub, codes = line.strip().split("|")
            codes = [c.strip() for c in codes.split(",") if c.strip()]
            uses[-1]["subs"].append(sub)
            uses[-1]["n"] += len(codes)
            seen += codes
            for c in codes:
                if c in by_slug:
                    by_slug[c]["use"], by_slug[c]["sub"] = uses[-1]["name"], sub
        else:
            name, en, ic, ref = line.split("|")
            uses.append({"name": name, "en": en, "icon": ic, "ref": ref, "subs": [], "n": 0})

    dup = sorted({c for c in seen if seen.count(c) > 1})
    if dup:
        raise SystemExit(f"USES で二つの細目に置かれた slug がある: {dup}")

    ghost = sorted(c for c in seen if c not in by_slug)
    if ghost:
        raise SystemExit(f"USES に ROWS に無い slug がある: {ghost}")

    out_slugs = [c.strip() for c in OUT.replace("\n", "").split(",") if c.strip()]
    stray = sorted(c for c in out_slugs if c not in by_slug)
    if stray:
        raise SystemExit(f"OUT に ROWS に無い slug がある: {stray}")

    # 行を足したときの入れ忘れを防ぐ。どこかの領域に置くか、出さないと決めるか。
    nowhere = sorted(c for c in by_slug if c not in seen and c not in out_slugs)
    if nowhere:
        raise SystemExit(f"USES にも OUT にも無い slug がある: {nowhere}")

    names = {u["name"] for u in uses}
    bad = sorted({w["use"] for w in wants if w["use"] and w["use"] not in names})
    if bad:
        raise SystemExit(f"WANTS の領域が領域名に無い: {bad}")
    bad = sorted({w["state"] for w in wants if w["state"] not in ("", "いま")})
    if bad:
        raise SystemExit(f"WANTS の状態は空か「いま」だけ: {bad}")

    here = Path(__file__).resolve().parent
    check_icons(here, [u["icon"] for u in uses] + ALWAYS)

    # 写真は images/<slug>.jpg に置いてあれば拾う。items.json は生成物なので、
    # 写真があるかどうかはファイルの側で決める（誰も items.json に書き戻さない）。
    for it in items + wants:
        if (here / "images" / (it["slug"] + ".jpg")).exists():
            it["img"] = f"images/{it['slug']}.jpg"

    data = {
        "note": NOTE,
        "items": [{k: v for k, v in i.items() if v} for i in items],
        "wants": [{k: v for k, v in w.items() if v} for w in wants],
        "uses": uses,
        "left": LEFT,
    }
    (here / "items.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"items.json を書いた（{len(items)}件・お気に入り{len(PICKS)}件・これから{len(wants)}件）")
    print(stamp_assets(here))


if __name__ == "__main__":
    main()
