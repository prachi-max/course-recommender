(function () {
  "use strict";

  const searchInput = document.getElementById("compare-search-input");
  const searchResults = document.getElementById("compare-search-results");
  const chipsEl = document.getElementById("compare-chips");
  const emptyEl = document.getElementById("compare-empty");
  const tableWrap = document.getElementById("compare-table-wrap");

  const allCourses = JSON.parse(document.getElementById("all-courses").textContent);
  const coursesById = {};
  allCourses.forEach(function (c) { coursesById[c.course_id] = c; });

  const MAX_COMPARE = 3;
  let selectedIds = [];

  const ROWS = [
    { label: "Category", get: function (c) { return c.category; } },
    { label: "Level", get: function (c) { return c.level; } },
    { label: "Rating", get: function (c) { return c.rating.toFixed(1) + " / 5"; }, num: function (c) { return c.rating; }, higherBetter: true },
    { label: "Students", get: function (c) { return c.students.toLocaleString(); }, num: function (c) { return c.students; }, higherBetter: true },
    { label: "Duration", get: function (c) { return c.duration_hours + "h"; }, num: function (c) { return c.duration_hours; }, higherBetter: false },
    { label: "Offered by", get: function (c) { return c.instructor; } },
    { label: "Skills", get: function (c) { return c.skills.join(", "); } },
  ];

  function renderChips() {
    chipsEl.innerHTML = selectedIds.map(function (id) {
      const c = coursesById[id];
      if (!c) return "";
      return '<span class="known-chip">' + escapeHtml(c.title) + ' <button type="button" data-id="' + id + '">&times;</button></span>';
    }).join("");
    chipsEl.querySelectorAll("button").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const id = parseInt(btn.getAttribute("data-id"), 10);
        selectedIds = selectedIds.filter(function (x) { return x !== id; });
        renderChips();
        renderTable();
      });
    });
  }

  function renderTable() {
    if (selectedIds.length < 2) {
      emptyEl.style.display = "block";
      emptyEl.textContent = selectedIds.length === 0
        ? "Add 2 or more courses above to compare them."
        : "Add at least one more course to compare.";
      tableWrap.style.display = "none";
      return;
    }
    emptyEl.style.display = "none";
    tableWrap.style.display = "block";

    const cs = selectedIds.map(function (id) { return coursesById[id]; });

    let html = '<table class="compare-table"><thead><tr><th class="row-label">Course</th>';
    cs.forEach(function (c) {
      html += '<td class="course-col-head"><a href="/course/' + c.course_id + '" style="color:var(--text); text-decoration:none;">' + escapeHtml(c.title) + '</a></td>';
    });
    html += "</tr></thead><tbody>";

    ROWS.forEach(function (row) {
      let bestVal = null;
      if (row.num) {
        const vals = cs.map(row.num);
        bestVal = row.higherBetter ? Math.max.apply(null, vals) : Math.min.apply(null, vals);
      }
      html += '<tr><th class="row-label">' + row.label + "</th>";
      cs.forEach(function (c) {
        const isBest = row.num && row.num(c) === bestVal && cs.length > 1;
        html += '<td class="' + (isBest ? "best-value" : "") + '">' + escapeHtml(String(row.get(c))) + (isBest ? " &#10003;" : "") + "</td>";
      });
      html += "</tr>";
    });

    html += "</tbody></table>";
    tableWrap.innerHTML = html;
  }

  searchInput.addEventListener("input", function () {
    const q = searchInput.value.trim().toLowerCase();
    if (q.length < 2) { searchResults.classList.remove("show"); return; }
    const matches = allCourses.filter(function (c) {
      return c.title.toLowerCase().indexOf(q) !== -1 && selectedIds.indexOf(c.course_id) === -1;
    }).slice(0, 8);
    if (!matches.length) { searchResults.classList.remove("show"); return; }
    searchResults.innerHTML = matches.map(function (c) {
      return '<div class="course-search-item" data-id="' + c.course_id + '">' + escapeHtml(c.title) +
        ' <span style="color:var(--text-faint); font-size:11.5px;">&middot; ' + escapeHtml(c.category) + '</span></div>';
    }).join("");
    searchResults.classList.add("show");
    searchResults.querySelectorAll(".course-search-item").forEach(function (item) {
      item.addEventListener("click", function () {
        if (selectedIds.length >= MAX_COMPARE) {
          showToast("You can compare up to " + MAX_COMPARE + " courses — remove one first.", true);
          return;
        }
        const id = parseInt(item.getAttribute("data-id"), 10);
        if (selectedIds.indexOf(id) === -1) selectedIds.push(id);
        renderChips();
        renderTable();
        searchInput.value = "";
        searchResults.classList.remove("show");
      });
    });
  });
  document.addEventListener("click", function (e) {
    if (!searchResults.contains(e.target) && e.target !== searchInput) searchResults.classList.remove("show");
  });

  renderChips();
  renderTable();
})();
