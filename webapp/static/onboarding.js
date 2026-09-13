(function () {
  "use strict";

  const nameInput = document.getElementById("name-input");
  const levelButtons = document.querySelectorAll("#level-segmented button");
  const categoryChips = document.querySelectorAll("#category-chips .chip-toggle");
  const skillChips = document.querySelectorAll("#skill-chips .chip-toggle");
  const searchInput = document.getElementById("course-search-input");
  const searchResults = document.getElementById("course-search-results");
  const knownChipsEl = document.getElementById("known-chips");
  const saveBtn = document.getElementById("save-profile-btn");
  const resetBtn = document.getElementById("reset-profile-btn");
  const note = document.getElementById("onboard-note");

  const allCourses = JSON.parse(document.getElementById("all-courses").textContent);
  const initialKnownIds = JSON.parse(document.getElementById("known-ids").textContent);
  const initialInterests = JSON.parse(document.getElementById("profile-data").textContent);
  const coursesById = {};
  allCourses.forEach(function (c) { coursesById[c.course_id] = c; });

  let selectedLevel = window.ONBOARD_SKILL_LEVEL || "";
  let knownIds = initialKnownIds.slice();

  // ---- skill level ----
  function renderLevel() {
    levelButtons.forEach(function (btn) {
      btn.classList.toggle("selected", btn.getAttribute("data-value") === selectedLevel);
    });
  }
  levelButtons.forEach(function (btn) {
    btn.addEventListener("click", function () {
      const v = btn.getAttribute("data-value");
      selectedLevel = selectedLevel === v ? "" : v;
      renderLevel();
    });
  });
  renderLevel();

  // ---- interest / skill chips ----
  function initChips(nodeList) {
    nodeList.forEach(function (chip) {
      const v = chip.getAttribute("data-value");
      if (initialInterests.indexOf(v) !== -1) chip.classList.add("selected");
      chip.addEventListener("click", function () { chip.classList.toggle("selected"); });
    });
  }
  initChips(categoryChips);
  initChips(skillChips);

  function selectedValues(nodeList) {
    return Array.prototype.filter.call(nodeList, function (c) { return c.classList.contains("selected"); })
      .map(function (c) { return c.getAttribute("data-value"); });
  }

  // ---- known-courses search ----
  function renderKnownChips() {
    if (!knownIds.length) {
      knownChipsEl.innerHTML = "";
      return;
    }
    knownChipsEl.innerHTML = knownIds.map(function (id) {
      const c = coursesById[id];
      if (!c) return "";
      return '<span class="known-chip">' + escapeHtml(c.title) + ' <button type="button" data-id="' + id + '">&times;</button></span>';
    }).join("");
    knownChipsEl.querySelectorAll("button").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const id = parseInt(btn.getAttribute("data-id"), 10);
        knownIds = knownIds.filter(function (x) { return x !== id; });
        renderKnownChips();
      });
    });
  }
  renderKnownChips();

  searchInput.addEventListener("input", function () {
    const q = searchInput.value.trim().toLowerCase();
    if (q.length < 2) { searchResults.classList.remove("show"); return; }
    const matches = allCourses.filter(function (c) {
      return c.title.toLowerCase().indexOf(q) !== -1 && knownIds.indexOf(c.course_id) === -1;
    }).slice(0, 8);
    if (!matches.length) { searchResults.classList.remove("show"); return; }
    searchResults.innerHTML = matches.map(function (c) {
      return '<div class="course-search-item" data-id="' + c.course_id + '">' + escapeHtml(c.title) +
        ' <span style="color:var(--text-faint); font-size:11.5px;">&middot; ' + escapeHtml(c.category) + '</span></div>';
    }).join("");
    searchResults.classList.add("show");
    searchResults.querySelectorAll(".course-search-item").forEach(function (item) {
      item.addEventListener("click", function () {
        const id = parseInt(item.getAttribute("data-id"), 10);
        if (knownIds.indexOf(id) === -1) knownIds.push(id);
        renderKnownChips();
        searchInput.value = "";
        searchResults.classList.remove("show");
      });
    });
  });
  document.addEventListener("click", function (e) {
    if (!searchResults.contains(e.target) && e.target !== searchInput) searchResults.classList.remove("show");
  });

  // ---- save ----
  saveBtn.addEventListener("click", function () {
    const interests = selectedValues(categoryChips).concat(selectedValues(skillChips));
    if (!interests.length && !knownIds.length) {
      note.textContent = "Pick at least one interest, or one course you already know.";
      note.style.color = "var(--accent)";
      return;
    }
    saveBtn.disabled = true;
    saveBtn.textContent = "Saving…";
    fetch("/api/profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: nameInput.value.trim() || "Learner",
        interests: interests,
        skill_level: selectedLevel || null,
        known_course_ids: knownIds,
      }),
    })
      .then(function (res) { return res.json().then(function (b) { return { ok: res.ok, body: b }; }); })
      .then(function (r) {
        if (!r.ok) {
          saveBtn.disabled = false;
          saveBtn.textContent = window.ONBOARD_IS_EDIT ? "Save Changes" : "Show My Recommendations";
          note.textContent = r.body.message || "Something went wrong.";
          note.style.color = "var(--accent)";
          return;
        }
        window.location.href = window.ONBOARD_IS_EDIT ? "/profile" : "/recommendations";
      })
      .catch(function (err) {
        saveBtn.disabled = false;
        saveBtn.textContent = window.ONBOARD_IS_EDIT ? "Save Changes" : "Show My Recommendations";
        showToast("Network error: " + err, true);
      });
  });

  if (resetBtn) {
    resetBtn.addEventListener("click", function () {
      if (!window.confirm("Reset your profile? This clears your interests and learning history.")) return;
      fetch("/api/profile/reset", { method: "POST" })
        .then(function () { window.location.href = "/onboarding"; })
        .catch(function (err) { showToast("Network error: " + err, true); });
    });
  }
})();
