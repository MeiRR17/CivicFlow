"""Build a dependency-free, static and searchable civic case dashboard."""
from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path
import shutil

from .analyze import load_observations
from .cases import load_cases, safe_url

ROOT = Path(__file__).resolve().parent.parent

STATUS_HE = {
    "reported": "דווח", "investigating": "בבדיקה", "proposed": "הוצע פתרון",
    "in_progress": "בטיפול", "evaluating": "במדידת תוצאות", "resolved": "נסגר לאחר אימות"
}
EVIDENCE_HE = {"synthetic": "תרחיש מדומה", "unverified": "טרם אומת", "documented": "נתמך במקורות"}


def _e(value: object) -> str:
    return escape(str(value), quote=True)


def _list(items: list[str]) -> str:
    return "".join(f"<li>{_e(item)}</li>" for item in items)


def _case_card(case: dict, metric: dict | None, max_delay: float) -> str:
    delay = float(metric["excess_vehicle_minutes"]) if metric else 0
    width = round(100 * delay / max_delay, 1) if max_delay > 0 else 0
    detail = (
        f'<span class="delay">{delay:,.0f} דקות־רכב עודפות*</span>' if metric
        else '<span class="delay empty">טרם הוזנו זמני נסיעה</span>'
    )
    sources = "".join(
        f'<a href="{_e(url)}" rel="noopener noreferrer" target="_blank">מקור {_e(i)}</a>'
        for i, url in enumerate(case.get("sources", []), start=1) if safe_url(url)
    ) or "<span>אין עדיין מקורות מאומתים</span>"
    updates = case.get("updates", [])
    last = updates[-1] if updates else None
    recent = (f'<p class="update">עדכון: {_e(last["date"])} · {_e(last["note"])}</p>'
              if last else "")
    searchable = " ".join(str(case.get(k, "")) for k in ("title", "location", "problem", "id", "site_id"))
    return f'''<article class="case-card" data-status="{_e(case['status'])}" data-search="{_e(searchable.lower())}">
      <div class="case-top"><span class="case-id">{_e(case['id'])}</span>
        <span class="status status-{_e(case['status'])}">{_e(STATUS_HE[case['status']])}</span></div>
      <h3>{_e(case['title'])}</h3>
      <p class="location">{_e(case['location'])} · {_e(case['site_id'])}</p>
      <p class="problem">{_e(case['problem'])}</p>
      <div class="meter-label">{detail}<span>{_e(EVIDENCE_HE[case['evidence_status']])}</span></div>
      <div class="meter"><span style="width:{width}%"></span></div>
      <details><summary>חקירה, אפשרויות פעולה ומעקב</summary>
        <div class="detail-grid"><section><h4>השערות — לא ממצאים</h4><ul>{_list(case['hypotheses'])}</ul></section>
        <section><h4>התערבויות לבדיקה</h4><ul>{_list(case['interventions'])}</ul></section></div>
        <p><strong>הגורם האחראי:</strong> {_e(case.get('responsible_body', 'טרם זוהה'))}</p>
        <p><strong>הצעד הבא:</strong> {_e(case['next_action'])}</p>
        <div class="sources"><strong>ראיות:</strong> {sources}</div>{recent}
      </details>
    </article>'''


def render_html(data: dict, observations: list[dict]) -> str:
    cases = data["cases"]
    metrics = {}
    for observation in observations:
        site = observation["site_id"]
        if site not in metrics or observation["excess_vehicle_minutes"] > metrics[site]["excess_vehicle_minutes"]:
            metrics[site] = observation
    max_delay = max((r["excess_vehicle_minutes"] for r in observations), default=0)
    is_demo = data["dataset_type"] == "synthetic"
    demo_text = ("סביבת הדגמה: כל התיקים והמספרים בדויים. אין להסיק מהם מסקנות על כבישי ישראל."
                 if is_demo else
                 "נתונים אמיתיים: כל ממצא דורש בדיקת מקור, ייצוגיות ואימות עצמאי.")
    counts = {s: sum(1 for case in cases if case["status"] == s) for s in STATUS_HE}
    options = "".join(f'<option value="{_e(s)}">{_e(he)} ({counts[s]})</option>' for s, he in STATUS_HE.items())
    cards = "\n".join(_case_card(case, metrics.get(case["site_id"]), max_delay) for case in cases)
    return f'''<!doctype html>
<html lang="he" dir="rtl"><head><meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<meta name="description" content="CivicFlow — חקירת בעיות ציבוריות, נתונים ופתרונות מדידים" />
<title>CivicFlow | מעבדת חקירה אזרחית</title>
<link rel="stylesheet" href="assets/style.css" /></head>
<body><a class="skip-link" href="#cases">דלג לתיקי החקירה</a>
<header class="hero"><div class="wrap"><nav class="top-nav" aria-label="ניווט ראשי">
<a class="wordmark" href="./" aria-label="CivicFlow, דף הבית"><span class="logo">CF</span> CivicFlow</a>
<div class="top-links"><a href="#method">מתודולוגיה</a><a href="#cases">תיקים פתוחים</a>
<a href="https://github.com/MeiRR17/CivicFlow" target="_blank" rel="noopener noreferrer">GitHub ↗</a></div></nav>
<div class="hero-body"><div class="eyebrow">CIVIC INVESTIGATION LAB · ISRAEL</div>
<h1>בעיות ציבוריות.<br /><em>תשובות מבוססות ראיות.</em></h1>
<p>מזהים צווארי בקבוק, בוחנים סיבות שורש, מתעדים חלופות ומודדים שינוי. מתחילים בתחבורה — ומפתחים מתודולוגיה לכל תחום.</p>
<div class="hero-actions"><a class="button-primary" href="#cases">לצפייה בתיקים</a>
<a class="button-secondary" href="https://github.com/MeiRR17/CivicFlow/issues/new" target="_blank" rel="noopener noreferrer">הציעו נושא לחקירה</a></div>
</div><div class="notice" role="status"><strong>{'נתוני הדגמה' if is_demo else 'נתונים ממקורות'}</strong><span>{_e(demo_text)}</span></div>
</div></header>
<main class="wrap"><section class="overview" aria-label="תמונת מצב">
<div class="stat"><span>תיקי חקירה</span><strong>{len(cases)}</strong><small>ניתנים למעקב</small></div>
<div class="stat"><span>אתרים לתיעדוף</span><strong>{len(metrics)}</strong><small>לפי תצפיות הזמינות במערכת</small></div>
<div class="stat"><span>תיקים בבדיקה</span><strong>{counts['investigating']}</strong><small>מעקב פתוח</small></div>
<div class="stat"><span>תיקים עם ראיות מתועדות</span><strong>{sum(c['evidence_status']=='documented' for c in cases)}</strong><small>מקורות מפורשים בלבד</small></div>
</section>
<section id="cases" class="cases-section"><div class="section-head"><div><p class="kicker">CASE TRACKER / 01</p>
<h2>מפת התחקירים</h2><p>מרשם שקוף של בעיות, השערות, פתרונות וצעדים הבאים.</p></div>
<span class="counter" id="visible-count" aria-live="polite">{len(cases)} תיקים</span></div>
<div class="filters"><label class="search-wrap"><span>חיפוש בתיקים</span><input id="search" type="search" placeholder="חיפוש לפי אזור, מזהה או נושא" /></label>
<label class="filter-wrap"><span>מצב טיפול</span><select id="status-filter"><option value="">כל המצבים</option>{options}</select></label></div>
<div id="case-grid" class="case-grid">{cards}</div>
<p id="empty-state" class="empty-state" hidden>לא נמצאו תיקים התואמים לסינון.</p>
<p class="footnote">* מדד סינון ניסיוני: (זמן נסיעה נצפה פחות זמן נסיעה בזרימה חופשית) × מספר כלי רכב באותו מסלול וחלון מדידה. אינו מבטא סיבתיות או ערך שנתי; אין להשוות בין חלונות לא תואמים.</p>
</section>
<section id="method" class="method-section"><div class="section-head"><div><p class="kicker">OUR METHOD / 02</p>
<h2>מהתלונה ועד לתוצאה</h2></div></div><div class="steps">
<div><span>01</span><h3>איסוף מבוקר</h3><p>נתוני מקור, תצפיות שטח, תוקף ורישוי. הפרדה בין דיווח למדידה.</p></div>
<div><span>02</span><h3>אבחון מערכתי</h3><p>בדיקת המקטע המקומי והשפעות במעלה ובמורד הרשת. השערות בנפרד מעובדות.</p></div>
<div><span>03</span><h3>חלופות והתערבות</h3><p>השוואת עלות, בטיחות, נגישות, זמן נסיעה והשפעות משניות.</p></div>
<div><span>04</span><h3>אחריות ובקרה</h3><p>איתור בעל הסמכות, פנייה מתועדת, תגובה ומדידת לפני/אחרי.</p></div></div></section>
</main><footer><div class="wrap"><strong>CivicFlow</strong><span>יוזמה אזרחית עצמאית. אין זיקה רשמית למשרד התחבורה או לרשות ציבורית.</span>
<a href="https://github.com/MeiRR17/CivicFlow">הקוד והמתודולוגיה פתוחים לעיון</a></div></footer>
<script src="assets/app.js" defer></script></body></html>'''


def build(observations_path: Path, cases_path: Path, output: Path) -> None:
    observations = load_observations(observations_path)
    data = load_cases(cases_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_html(data, observations), encoding="utf-8")
    assets = output.parent / "assets"
    assets.mkdir(exist_ok=True)
    for filename in ("style.css", "app.js"):
        shutil.copyfile(ROOT / "web" / filename, assets / filename)
    (output.parent / "report.json").write_text(json.dumps({
        "dataset_type": data["dataset_type"], "observation_count": len(observations),
        "case_count": len(data["cases"]), "ranked_observations": observations
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observations", type=Path, default=ROOT / "data/example_observations.csv")
    parser.add_argument("--cases", type=Path, default=ROOT / "data/cases.json")
    parser.add_argument("--output", type=Path, default=ROOT / "docs/index.html")
    args = parser.parse_args()
    build(args.observations, args.cases, args.output)
    print(f"Built {args.output}")


if __name__ == "__main__":
    main()
