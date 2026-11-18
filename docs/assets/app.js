"use strict";
(() => {
  const search = document.getElementById("search");
  const status = document.getElementById("status-filter");
  const cases = Array.from(document.querySelectorAll(".case-card"));
  const counter = document.getElementById("visible-count");
  const empty = document.getElementById("empty-state");

  function filterCases() {
    const query = search.value.trim().toLocaleLowerCase("he");
    let shown = 0;
    for (const card of cases) {
      const matched = (!query || card.dataset.search.includes(query)) &&
        (!status.value || card.dataset.status === status.value);
      card.hidden = !matched;
      if (matched) shown += 1;
    }
    counter.textContent = `${shown} תיקים`;
    empty.hidden = shown !== 0;
  }
  search.addEventListener("input", filterCases);
  status.addEventListener("change", filterCases);
})();
