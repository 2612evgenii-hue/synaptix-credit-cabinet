#!/usr/bin/env python3
"""Build offline indexes from the saved, sanitized browser observations."""

from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit, urlunsplit


HERE = Path(__file__).resolve().parent
GUIDE = HERE.parents[1] / "alfa-design-guide.md"
MARKER = "<!-- GENERATED MEASUREMENTS -->"


def read(name):
    return json.loads((HERE / name).read_text())


def write(name, data):
    (HERE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def normalized(url):
    parts = urlsplit(url)
    path = re.sub(r"/+", "/", parts.path)
    return urlunsplit((parts.scheme, parts.netloc, path, "", ""))


def viewport(record):
    value = record["viewport"]
    return value.get("width", value.get("w")), value.get("height", value.get("h"))


def mode(record):
    if record.get("test_mode"):
        return record["test_mode"]
    width, _ = viewport(record)
    if record["viewport"].get("scrollWidth", width) > width + 5:
        return "narrow document; horizontal overflow observed"
    if "mobile-profile" in record["key"] or record["key"].startswith("home-mobile"):
        return "Android Chrome mobile document"
    return "desktop document" if width >= 1024 else "resized document"


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def main():
    records = read("measurements.json") + read("extended-measurements.json")
    by_key = {record["key"]: record for record in records}
    by_url = defaultdict(list)
    for record in records:
        by_url[normalized(record["url"])].append(record)

    redirects = {}
    for entry in read("navigation-map.json"):
        observed = by_key.get(entry["recordKey"])
        if observed:
            redirects[normalized(entry["requested"])] = normalized(observed["url"])

    found = {}
    for name in ("sitemap-links.json", "home-links.json", "future-links.json"):
        for entry in read(name):
            # Preserve original sitemap URLs to keep its reported cardinality auditable.
            found.setdefault(entry["url"], entry.get("text", ""))
    for url in by_url:
        found.setdefault(url, "")
    found["https://online.alfabank.ru/"] = "Онлайн-банк"
    found["https://digital.alfabank.ru/techradar"] = "Техрадар"

    with (HERE / "coverage.csv").open("w", newline="", encoding="utf-8") as stream:
        fields = ["url", "label", "status", "observed_url", "viewports", "record_keys"]
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for original, label in sorted(found.items()):
            canonical = normalized(original)
            actual = redirects.get(canonical, canonical)
            observations = by_url.get(actual, [])
            if observations:
                status = "measured"
                if actual != canonical:
                    status = "redirect observed and destination measured"
                if actual.startswith("https://id.alfabank.ru/"):
                    status = "measured login error state only"
            elif original in ("https://online.alfabank.ru/", "https://digital.alfabank.ru/techradar"):
                status = "upstream connection error; no product style measured"
            else:
                status = "discovered; not individually inspected"
            writer.writerow({
                "url": original, "label": " ".join(label.split()), "status": status,
                "observed_url": actual if observations else "",
                "viewports": "; ".join(sorted({f"{viewport(r)[0]}x{viewport(r)[1]}" for r in observations})),
                "record_keys": "; ".join(r["key"] for r in observations),
            })

    definitions = read("official-design-tokens.json")["files"]
    summary = {
        "date": "2026-10-20",
        "valid_observations": len(records),
        "distinct_measured_urls": len(by_url),
        "sitemap_unique_original_urls": len({x["url"] for x in read("sitemap-links.json")}),
        "sitemap_unique_normalized_urls": len({normalized(x["url"]) for x in read("sitemap-links.json")}),
        "coverage_catalog_urls": len(found),
        "viewports": sorted({f"{viewport(r)[0]}x{viewport(r)[1]}" for r in records}),
        "screenshots": len(list((HERE / "screenshots").glob("*.jpg"))),
        "token_source_files": len(definitions),
        "token_definitions": sum(len(x["tokens"]) for x in definitions),
        "bank_css_stylesheets": len(read("home-css-details.json")),
        "user_provided_mobile_images_reviewed": read("mobile-image-observations.json")["source_image_count"],
        "user_provided_mobile_images_vendored": 0,
        "scope": "Public sampled interfaces and explicit demo; no claim of all 1413 pages or authenticated product states",
        "sampling": "Computed samples include mounted offscreen nodes; bounded headings/controls/panels. No complete CSS inventory for every route.",
    }
    write("research-summary.json", summary)

    appendix = [MARKER, "", f"Сохранено **{len(records)} наблюдений для {len(by_url)} разных URL**. "
                f"В каталоге публичных исходников — **{summary['token_definitions']} определений**. "
                "Число наблюдений включает разные размеры и состояния одной страницы.", ""]
    for url, observations in sorted(by_url.items()):
        parts = urlsplit(url)
        appendix += [f"### {cell(parts.netloc + parts.path)}", "", f"[Открыть источник]({url})", "",
                     "| Запись | Viewport | Способ проверки | Первые текстовые уровни |",
                     "| --- | --- | --- | --- |"]
        for record in observations:
            width, height = viewport(record)
            headings = []
            for heading in record.get("headings", [])[:2]:
                style = heading["style"]
                family = style["fontFamily"].split(",")[0].strip('"')
                headings.append(f"{heading['tag']}: {family}, {style['fontSize']} / {style['lineHeight']}, {style['fontWeight']}")
            appendix.append(f"| `{cell(record['key'])}` | {width} × {height} | {cell(mode(record))} | {cell('; '.join(headings) or 'Нет в ограниченной выборке')} |")
        representative = next((r for r in observations if viewport(r)[0] >= 1024 and r.get("panels")), observations[0])
        panels = representative.get("panels", [])[:3]
        if panels:
            appendix += ["", "Образцы контейнеров из указанной записи; применять с учётом их роли и расположения:", "",
                         "| Запись | Образец | Ширина | Радиус | Padding | Заливка |",
                         "| --- | --- | --- | --- | --- | --- |"]
            for index, panel in enumerate(panels, 1):
                style, rect = panel["style"], panel["rect"]
                appendix.append(f"| `{cell(representative['key'])}` | {index} | {rect.get('width', rect.get('w'))} px | {cell(style['borderRadius'])} | {cell(style['padding'])} | {cell(style['backgroundColor'])} |")
        appendix.append("")

    appendix += ["## Каталог публичных файлов токенов", "",
                 "Это определения библиотеки, а не перечень применённых на каждом сайте цветов. Повторные имена в разных файлах и темах учитываются как отдельные определения.", "",
                 "| Файл | Определений |",
                 "| --- | --- |"]
    for definition in sorted(definitions, key=lambda x: x["path"]):
        appendix.append(f"| [{cell(definition['path'])}]({definition['url']}) | {len(definition['tokens'])} |")
    appendix += ["", "## Визуальная подборка", "",
                 "Скриншоты получены из публичных страниц и обозначенного банком демо. Баннеры могут меняться автоматически. Подборка помогает сравнивать направления, но не заменяет CSS-замеры.", "",
                 "![Сравнение визуальных направлений Альфа-Банка](research/alfa-2026-10-20/contact-sheet.jpg)", ""]
    current = GUIDE.read_text().split(MARKER)[0].rstrip()
    GUIDE.write_text(current + "\n\n" + "\n".join(appendix))

    entries = []
    for file in sorted(HERE.rglob("*")):
        if file.is_file() and file.name != "manifest.json" and "__pycache__" not in file.parts:
            content = file.read_bytes()
            entries.append({"file": str(file.relative_to(HERE)), "bytes": len(content),
                            "sha256": hashlib.sha256(content).hexdigest()})
    write("manifest.json", {"date": "2026-10-20", "files": entries})
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
