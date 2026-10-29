#!/usr/bin/env python3
"""さいはてラボ 静的サイトビルダー

posts/*.md と pages/*.md を読み込み、dist/ にHTMLを書き出す。
- frontmatter の status が "published" の記事だけを公開する（"draft" は出力しない）
- 依存: Markdown, PyYAML（requirements.txt）
"""
import html
import re
import shutil
import sys
from datetime import date, datetime
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).parent
DIST = ROOT / "dist"

SITE = {
    "name": "さいはてラボ",
    "tagline": "道東発、ローカル×AI通信",
    "description": "北海道・道東の現場から、AIで地域を動かす実践記とローカル情報を届けるメディア。",
    "url": "https://saihate-lab.netlify.app",
}

CATEGORIES = {
    "ai": {"label": "AI実践記", "desc": "Claude Codeなどで作ったものの裏側と、地方でAIを使う実践の記録。"},
    "local": {"label": "道東ローカル", "desc": "浜中・釧路・根室あたりのイベント、店、季節のこと。"},
}

FRONT = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)


def load(path: Path):
    text = path.read_text(encoding="utf-8")
    m = FRONT.match(text)
    if not m:
        raise SystemExit(f"frontmatterがありません: {path}")
    meta = yaml.safe_load(m.group(1)) or {}
    body = m.group(2)
    # URLには日付を含めない（posts/2026-10-29-foo.md → /posts/foo/）
    meta["slug"] = meta.get("slug") or re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem)
    d = meta.get("date")
    if isinstance(d, str):
        d = datetime.strptime(d, "%Y-%m-%d").date()
    meta["date"] = d or date.today()
    meta["html"] = markdown.markdown(body, extensions=["extra", "toc", "sane_lists"])
    return meta


def esc(s):
    return html.escape(str(s or ""), quote=True)


def fmt_date(d):
    return f"{d.year}.{d.month:02d}.{d.day:02d}"


def layout(title, body, desc=None, path="/", hero=""):
    full_title = f"{title}｜{SITE['name']}" if title != SITE["name"] else f"{SITE['name']}｜{SITE['tagline']}"
    desc = desc or SITE["description"]
    nav = "".join(f'<a href="/category/{k}/">{v["label"]}</a>' for k, v in CATEGORIES.items())
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE['url']}{path}">
<link rel="canonical" href="{SITE['url']}{path}">
<link rel="alternate" type="application/rss+xml" title="{SITE['name']}" href="/feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&family=Zen+Old+Mincho:wght@600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/style.css">
</head>
<body>
<header class="site-header">
  <div class="wrap">
    <a class="logo" href="/"><span class="logo-mark" aria-hidden="true"></span>{SITE['name']}</a>
    <nav>{nav}<a href="/about/">このサイトについて</a><a class="nav-contact" href="/contact/">お問い合わせ</a></nav>
  </div>
</header>
{hero}
<main class="wrap">
{body}
</main>
<footer class="site-footer">
  <div class="wrap">
    <p class="foot-name">{SITE['name']}</p>
    <p>{SITE['tagline']}</p>
    <p class="foot-links"><a href="/about/">このサイトについて</a><a href="/contact/">お問い合わせ・お仕事のご相談</a><a href="/privacy/">プライバシーポリシー</a></p>
    <p class="small">当サイトの記事には、アフィリエイトなどの広告を含むものがあります。広告を含む記事には「PR」と表示しています。</p>
    <p class="small">© {date.today().year} {SITE['name']}</p>
  </div>
</footer>
</body>
</html>
"""


CTA = """<aside class="cta">
  <p class="cta-kicker">お仕事のご相談</p>
  <p class="cta-title">地域の「AIでやってみたい」を、一緒に形にします。</p>
  <p>PR動画やゲームの制作、ドローン撮影、イベントの企画、AIの使い方の相談など。まずはお気軽にどうぞ。</p>
  <a class="cta-btn" href="/contact/">相談してみる</a>
</aside>"""


CONTACT_FORM = """<form class="contact-form" name="contact" method="POST" action="/contact/thanks/" data-netlify="true" netlify-honeypot="company-url">
  <input type="hidden" name="form-name" value="contact">
  <p class="hp"><label>この欄は空のままにしてください <input name="company-url" id="company-url" tabindex="-1" autocomplete="off"></label></p>
  <div class="field">
    <label for="kind">ご用件</label>
    <select id="kind" name="kind" required>
      <option value="">選んでください</option>
      <option>お仕事のご相談（制作・撮影・企画など）</option>
      <option>取材・掲載のご依頼</option>
      <option>記事の内容について</option>
      <option>その他</option>
    </select>
  </div>
  <div class="field">
    <label for="name">お名前 <span class="req">必須</span></label>
    <input id="name" name="name" type="text" autocomplete="name" required>
  </div>
  <div class="field">
    <label for="org">ご所属（会社・団体名など）</label>
    <input id="org" name="org" type="text" autocomplete="organization">
  </div>
  <div class="field">
    <label for="email">メールアドレス <span class="req">必須</span></label>
    <input id="email" name="email" type="email" autocomplete="email" required>
  </div>
  <div class="field">
    <label for="message">内容 <span class="req">必須</span></label>
    <textarea id="message" name="message" rows="7" required placeholder="例：町のPR動画をAIで作れないか相談したいです。時期は来年の春ごろを考えています。"></textarea>
  </div>
  <p class="form-note">送信いただいた内容は、お問い合わせへの返信にのみ使います。詳しくは<a href="/privacy/">プライバシーポリシー</a>をご覧ください。</p>
  <button class="cta-btn" type="submit">送信する</button>
</form>"""


def card(p):
    cat = CATEGORIES.get(p.get("category"), {"label": ""})
    pr = '<span class="pr">PR</span>' if p.get("pr") else ""
    return f"""<article class="card">
  <a href="/posts/{p['slug']}/">
    <p class="meta"><span class="cat cat-{esc(p.get('category'))}">{cat['label']}</span>{pr}<time>{fmt_date(p['date'])}</time></p>
    <h2>{esc(p['title'])}</h2>
    <p class="excerpt">{esc(p.get('description'))}</p>
  </a>
</article>"""


def write(path: str, content: str):
    out = DIST / path.strip("/") / "index.html" if not path.endswith(".xml") else DIST / path.strip("/")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    shutil.copytree(ROOT / "assets", DIST / "assets")

    posts = [load(p) for p in sorted((ROOT / "posts").glob("*.md"))]
    # --drafts を付けると下書きも含めてプレビュー用にビルドする（本番では付けない）
    show_drafts = "--drafts" in sys.argv
    posts = [p for p in posts if p.get("status") == "published" or (show_drafts and p.get("status") == "draft")]
    posts.sort(key=lambda p: p["date"], reverse=True)

    # 記事ページ
    for p in posts:
        cat = CATEGORIES.get(p.get("category"), {"label": ""})
        pr_note = (
            '<p class="pr-note"><span class="pr">PR</span>この記事にはアフィリエイトリンクなどの広告が含まれます。</p>'
            if p.get("pr") else ""
        )
        related = [q for q in posts if q is not p and q.get("category") == p.get("category")][:3]
        rel_html = (
            '<section class="related"><h2>同じカテゴリの記事</h2>' + "".join(card(q) for q in related) + "</section>"
            if related else ""
        )
        body = f"""<article class="post">
  <p class="meta"><a class="cat cat-{esc(p.get('category'))}" href="/category/{esc(p.get('category'))}/">{cat['label']}</a><time>{fmt_date(p['date'])}</time></p>
  <h1>{esc(p['title'])}</h1>
  {pr_note}
  <div class="prose">{p['html']}</div>
</article>
{CTA}
{rel_html}"""
        write(f"/posts/{p['slug']}/", layout(p["title"], body, p.get("description"), f"/posts/{p['slug']}/"))

    # トップ
    hero = f"""<section class="hero"><div class="wrap">
  <p class="hero-kicker">{SITE['tagline']}</p>
  <h1>日本の東の端から、<br>AIで地域を動かす。</h1>
  <p>{SITE['description']}</p>
</div></section>"""
    listing = "".join(card(p) for p in posts) or '<p class="empty">記事を準備中です。</p>'
    write("/", layout(SITE["name"], f'<section class="list">{listing}</section>', hero=hero))

    # カテゴリ
    for key, c in CATEGORIES.items():
        items = [p for p in posts if p.get("category") == key]
        listing = "".join(card(p) for p in items) or '<p class="empty">記事を準備中です。</p>'
        body = f'<header class="page-head"><h1>{c["label"]}</h1><p>{c["desc"]}</p></header><section class="list">{listing}</section>'
        write(f"/category/{key}/", layout(c["label"], body, c["desc"], f"/category/{key}/"))

    # 固定ページ
    for f in sorted((ROOT / "pages").glob("*.md")):
        pg = load(f)
        html_body = pg["html"].replace("<p>{{form}}</p>", CONTACT_FORM)
        body = f'<article class="post"><h1>{esc(pg["title"])}</h1><div class="prose">{html_body}</div></article>'
        write(f"/{pg['slug']}/", layout(pg["title"], body, pg.get("description"), f"/{pg['slug']}/"))

    # 404
    nf = """<article class="post notfound">
  <p class="hero-kicker">404</p>
  <h1>ページが見つかりませんでした</h1>
  <div class="prose"><p>お探しのページは、移動したか削除された可能性があります。URLに間違いがないかもご確認ください。</p>
  <p><a class="cta-btn" href="/">トップページへ</a></p></div>
</article>"""
    (DIST / "404.html").write_text(layout("ページが見つかりません", nf, path="/404.html"), encoding="utf-8")

    # RSS
    items = "".join(
        f"<item><title>{esc(p['title'])}</title><link>{SITE['url']}/posts/{p['slug']}/</link>"
        f"<guid>{SITE['url']}/posts/{p['slug']}/</guid><pubDate>{p['date'].strftime('%a, %d %b %Y 00:00:00 +0900')}</pubDate>"
        f"<description>{esc(p.get('description'))}</description></item>"
        for p in posts[:20]
    )
    (DIST / "feed.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{SITE["name"]}</title>'
        f'<link>{SITE["url"]}/</link><description>{esc(SITE["description"])}</description>{items}</channel></rss>',
        encoding="utf-8",
    )

    # sitemap
    urls = ["/", "/about/", "/contact/", "/privacy/"] + [f"/category/{k}/" for k in CATEGORIES] + [f"/posts/{p['slug']}/" for p in posts]
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(f"<url><loc>{SITE['url']}{u}</loc></url>" for u in urls)
        + "</urlset>",
        encoding="utf-8",
    )
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE['url']}/sitemap.xml\n", encoding="utf-8")

    print(f"built {len(posts)} posts -> dist/")


if __name__ == "__main__":
    main()
