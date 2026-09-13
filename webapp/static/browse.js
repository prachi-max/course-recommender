(function () {
  "use strict";

  const grid = document.getElementById("course-grid");
  const rows = document.getElementById("course-rows");
  const qInput = document.getElementById("q-input");
  const categorySelect = document.getElementById("category-select");
  const levelSelect = document.getElementById("level-select");
  const clearBtn = document.getElementById("clear-filters-btn");
  const filterCount = document.getElementById("filter-count");

  // Row order follows real catalog popularity (same data the "Explore by
  // Category" module uses), so the biggest tracks show up first.
  const categoryOrderEl = document.getElementById("category-counts-data");
  const categoryOrder = categoryOrderEl
    ? JSON.parse(categoryOrderEl.textContent).map(function (r) { return r.category; })
    : [];

  function hasActiveFilters() {
    return !!(qInput.value.trim() || categorySelect.value || levelSelect.value);
  }

  function groupByCategory(courses) {
    const byCat = {};
    courses.forEach(function (c) {
      (byCat[c.category] = byCat[c.category] || []).push(c);
    });
    const order = categoryOrder.length ? categoryOrder : Object.keys(byCat);
    return order
      .filter(function (cat) { return byCat[cat] && byCat[cat].length; })
      .map(function (cat) { return { category: cat, courses: byCat[cat] }; });
  }

  function renderRows(courses) {
    const groups = groupByCategory(courses);
    if (!groups.length) {
      rows.innerHTML = '<div class="empty-note">No courses match those filters. Try clearing one.</div>';
      return;
    }
    rows.innerHTML = groups.map(function (g, i) {
      const meta = categoryMeta(g.category);
      return (
        '<div class="course-row">' +
          '<div class="course-row-head">' +
            '<h3>' +
              '<span class="course-row-badge" style="background:' + meta.c1 + ';">' + iconSvg(meta.icon, 14) + "</span>" +
              escapeHtml(g.category) +
              '<span class="course-row-count">' + g.courses.length + " course" + (g.courses.length === 1 ? "" : "s") + "</span>" +
            "</h3>" +
            '<div class="course-row-nav">' +
              '<button type="button" class="course-row-btn" data-row="' + i + '" data-dir="-1" aria-label="Scroll left">' + iconSvg("chevron-left", 15) + "</button>" +
              '<button type="button" class="course-row-btn" data-row="' + i + '" data-dir="1" aria-label="Scroll right">' + iconSvg("chevron-right", 15) + "</button>" +
            "</div>" +
          "</div>" +
          '<div class="course-row-scroller">' +
            '<div class="course-row-track" id="course-row-track-' + i + '">' +
              g.courses.map(function (c) { return renderCourseCard(c, { showStatus: true }); }).join("") +
            "</div>" +
          "</div>" +
        "</div>"
      );
    }).join("");
    wireStatusSelects(rows);
    rows.querySelectorAll(".course-row-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const track = document.getElementById("course-row-track-" + btn.getAttribute("data-row"));
        const dir = parseInt(btn.getAttribute("data-dir"), 10);
        track.scrollBy({ left: dir * 320, behavior: "smooth" });
      });
    });
  }

  function renderFlat(courses) {
    if (!courses.length) {
      grid.innerHTML = '<div class="empty-note">No courses match those filters. Try clearing one.</div>';
      return;
    }
    grid.innerHTML = courses.map(function (c) { return renderCourseCard(c, { showStatus: true }); }).join("");
    wireStatusSelects(grid);
  }

  function render(courses) {
    if (hasActiveFilters()) {
      rows.hidden = true;
      grid.hidden = false;
      renderFlat(courses);
    } else {
      grid.hidden = true;
      rows.hidden = false;
      renderRows(courses);
    }
    filterCount.textContent = courses.length + " course" + (courses.length === 1 ? "" : "s");
  }

  function fetchAndRender() {
    const params = new URLSearchParams();
    if (qInput.value.trim()) params.set("q", qInput.value.trim());
    if (categorySelect.value) params.set("category", categorySelect.value);
    if (levelSelect.value) params.set("level", levelSelect.value);
    fetch("/api/courses?" + params.toString())
      .then(function (res) { return res.json(); })
      .then(render)
      .catch(function (err) { showToast("Network error: " + err, true); });

    const url = new URL(window.location);
    url.search = params.toString();
    window.history.replaceState({}, "", url);
  }

  let debounceTimer;
  qInput.addEventListener("input", function () {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(fetchAndRender, 250);
  });
  categorySelect.addEventListener("change", fetchAndRender);
  levelSelect.addEventListener("change", fetchAndRender);
  clearBtn.addEventListener("click", function () {
    qInput.value = "";
    categorySelect.value = "";
    levelSelect.value = "";
    fetchAndRender();
  });

  // Render whatever the server already computed for the initial page load
  // (so the page has real content immediately, no fetch round-trip needed).
  const initial = JSON.parse(document.getElementById("initial-courses").textContent);
  render(initial);
})();
