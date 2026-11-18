# Contributing to CivicFlow

CivicFlow welcomes reproducible open-data analysis, methodology reviews, interface improvements and carefully documented field observations. It is not a platform for naming and shaming individuals.

1. Open a GitHub issue outlining a *specific, testable* research question. Do not attach plates, identifiable photos, personal GPS tracks or private contact information.
2. For real-world claims include a primary source URL, observation date, exact **public** road segment/direction and time window, methodology, limitations, and available contrary evidence.
3. Separate observations, hypotheses, engineering recommendations, agency responses and claimed outcomes. If you cannot verify a claim, mark it `unverified`.
4. Use structured case records in `data/cases.json`, keeping demonstration data explicitly `synthetic`. Build with `python -m src.build_site` and run `python -m unittest discover -s tests`.
5. Contributors should discuss disagreements through sources and methods. Maintainers may remove unsafe, personal, defamatory or undocumented material. Corrections should be dated and visible.

Do not upload raw confidential or personally identifying data. If a dataset's license is unclear, link to its official catalogue rather than redistributing it.
