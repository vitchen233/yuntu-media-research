#!/usr/bin/env python3
"""Create a local launch page for generated HTML research reports."""

import argparse
import html
from pathlib import Path


LABELS = {
    "01": ("实时选题调研", "从近3天真实作品找到可拍方向", "#9e95ff"),
    "02": ("对标账号分析", "用账号内基线识别反复有效的内容", "#54c8b1"),
    "03": ("内容结构拆解", "把单条视频拆成可复用的推进时间轴", "#de7d6b"),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory")
    parser.add_argument("--output", default="index.html")
    args = parser.parse_args()
    directory = Path(args.directory)
    reports = sorted(path for path in directory.glob("*.html") if path.name != args.output)
    cards = []
    for path in reports:
        key = path.name[:2]
        title, detail, color = LABELS.get(key, (path.stem, "研究报告", "#d7a96f"))
        cards.append(
            f'<a class="card" href="{html.escape(path.name, quote=True)}" style="--accent:{color}">'
            f'<span>{html.escape(key)}</span><h2>{html.escape(title)}</h2><p>{html.escape(detail)}</p><b>打开报告 ↗</b></a>'
        )
    output = directory / args.output
    output.write_text(f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>YUNTU MEDIA RESEARCH</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#090806;color:#f3efe8;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;letter-spacing:0}}main{{width:min(1180px,calc(100% - 40px));margin:auto;padding:72px 0}}header{{padding-bottom:54px;border-bottom:1px solid #34312b}}.brand{{color:#a8a39a;font-size:13px;font-weight:700}}h1{{font-size:clamp(48px,8vw,92px);line-height:1;margin:56px 0 22px;letter-spacing:0}}header p{{max-width:720px;color:#bdb7ad;font-size:18px;line-height:1.8}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:48px}}.card{{min-height:330px;padding:28px;border:1px solid #34312b;border-top:3px solid var(--accent);background:#151411;color:#f3efe8;text-decoration:none;display:flex;flex-direction:column;transition:transform .2s,border-color .2s}}.card:hover{{transform:translateY(-4px);border-color:var(--accent)}}.card>span{{color:var(--accent);font-weight:800}}.card h2{{margin:54px 0 14px;font-size:28px}}.card p{{color:#a8a39a;line-height:1.8}}.card b{{margin-top:auto;color:var(--accent)}}footer{{margin-top:72px;padding-top:24px;border-top:1px solid #34312b;color:#716d66;font-size:12px}}@media(max-width:760px){{.grid{{grid-template-columns:1fr}}}}
</style></head><body><main><header><div class="brand">YUNTU / MEDIA RESEARCH / REAL DATA</div><h1>一次任务，三份结果</h1><p>从实时发现，到账号判断，再到单条内容结构。所有页面均由真实RedFox调用与浏览器核对生成，可以离线打开。</p></header><section class="grid">{"".join(cards)}</section><footer>LOCAL RESEARCH BUNDLE · {len(cards)} REPORTS</footer></main></body></html>''', encoding="utf-8")
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
