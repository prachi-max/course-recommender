// Shared helpers used by every page: category visuals, card rendering,
// toasts, and the "add to My Learning" status control.

// Same self-drawn line-icon set as webapp/icons.py (kept in sync by hand -
// this is the small subset of icons that get built into HTML client-side,
// via renderCourseCard/renderCategoryGrid/renderContinueRow below, instead
// of server-rendered by Jinja).
const ICONS = {
  "book-open": '<path d="M12 6.2C10.6 5 8.6 4.3 5.8 4.3c-.6 0-1 .5-1 1v12c0 .5.4 1 1 1 2.8 0 4.8.7 6.2 2 1.4-1.3 3.4-2 6.2-2 .6 0 1-.5 1-1v-12c0-.5-.4-1-1-1-2.8 0-4.8.7-6.2 1.9Z"/><path d="M12 6.2v13"/>',
  "code": '<path d="m9 8-4.3 4L9 16M15 8l4.3 4L15 16"/>',
  "bar-chart": '<path d="M4 19V11M10 19V5M16 19v-7M21 19H3"/>',
  "cpu": '<rect x="7" y="7" width="10" height="10" rx="1.5"/><rect x="10.2" y="10.2" width="3.6" height="3.6"/><path d="M12 3.3v3M12 17.7v3M3.3 12h3M17.7 12h3"/>',
  "cloud": '<path d="M7.2 18.3a3.9 3.9 0 0 1-.5-7.8 5.4 5.4 0 0 1 10.6-1.2A4.1 4.1 0 0 1 16.9 18.3Z"/>',
  "shield": '<path d="M12 3.6 5.3 6v5.4c0 4.4 2.9 7.3 6.7 8.7 3.8-1.4 6.7-4.3 6.7-8.7V6Z"/>',
  "smartphone": '<rect x="7.2" y="3" width="9.6" height="18" rx="2"/><path d="M11 18.2h2"/>',
  "palette": '<path d="M12 3.7a8.3 8.3 0 1 0 0 16.6c1 0 1.7-.8 1.7-1.7 0-.5-.2-.9-.5-1.2a1.5 1.5 0 0 1 1.1-2.6h1.8a3.7 3.7 0 0 0 3.6-3.7c0-4.1-3.5-7.4-7.7-7.4Z"/><circle cx="7.6" cy="11" r="1" fill="currentColor" stroke="none"/><circle cx="9.6" cy="7.6" r="1" fill="currentColor" stroke="none"/><circle cx="14.4" cy="7.2" r="1" fill="currentColor" stroke="none"/><circle cx="16.3" cy="10.6" r="1" fill="currentColor" stroke="none"/>',
  "briefcase": '<rect x="3.5" y="8" width="17" height="10.8" rx="1.5"/><path d="M8.5 8V6.2a2 2 0 0 1 2-2h3a2 2 0 0 1 2 2V8"/><path d="M3.5 13h17"/>',
  "server": '<rect x="4" y="4.3" width="16" height="6" rx="1.3"/><rect x="4" y="13.7" width="16" height="6" rx="1.3"/><path d="M7.3 7.3h.01M7.3 16.7h.01"/>',
  "database": '<ellipse cx="12" cy="6" rx="7" ry="2.6"/><path d="M5 6v12c0 1.4 3.1 2.6 7 2.6s7-1.2 7-2.6V6"/><path d="M5 12c0 1.4 3.1 2.6 7 2.6s7-1.2 7-2.6"/>',
  "chevron-left": '<path d="M14.5 5.5 8 12l6.5 6.5"/>',
  "chevron-right": '<path d="M9.5 5.5 16 12l-6.5 6.5"/>',
};

function iconSvg(name, size) {
  size = size || 16;
  const inner = ICONS[name] || ICONS["book-open"];
  return '<svg width="' + size + '" height="' + size + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
    'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + inner + "</svg>";
}

// Larger, two-tone "flat icon" versions of the same category set, used only
// for the course-card banner tile (renderCourseCard below) where there's
// room for real detail - filled shapes plus a lighter tint of the same
// color, the way a small app/logo icon is usually drawn, rather than the
// thin single-stroke glyphs used everywhere else in the UI.
const BANNER_ICONS = {
  "code": '<rect x="2.5" y="4" width="19" height="16" rx="2.6" fill="currentColor" fill-opacity=".14"/>' +
    '<path d="M2.5 8.4h19" stroke="currentColor" stroke-width="1.5"/>' +
    '<circle cx="5.4" cy="6.2" r=".7" fill="currentColor"/><circle cx="7.3" cy="6.2" r=".7" fill="currentColor"/><circle cx="9.2" cy="6.2" r=".7" fill="currentColor"/>' +
    '<path d="m9.3 12.8-2.6 2.6 2.6 2.6M14.7 12.8l2.6 2.6-2.6 2.6" stroke="currentColor" stroke-width="1.7" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
  "bar-chart": '<rect x="3.8" y="13" width="3.6" height="7.3" rx="1" fill="currentColor" fill-opacity=".3"/>' +
    '<rect x="10.2" y="7.8" width="3.6" height="12.5" rx="1" fill="currentColor" fill-opacity=".3"/>' +
    '<rect x="16.6" y="4" width="3.6" height="16.3" rx="1" fill="currentColor" fill-opacity=".3"/>' +
    '<path d="M4 15.8 10 10.6 14 13.2 20 6.2" stroke="currentColor" stroke-width="1.9" fill="none" stroke-linecap="round" stroke-linejoin="round"/>' +
    '<circle cx="20" cy="6.2" r="1.7" fill="currentColor"/>',
  "cpu": '<path d="M9.3 4.2a3.1 3.1 0 0 0-3.1 3.1v.3a2.9 2.9 0 0 0-1.5 5 2.9 2.9 0 0 0 1.7 5 3.1 3.1 0 0 0 2.9 2.1h.4V4.2Z" fill="currentColor" fill-opacity=".26"/>' +
    '<path d="M14.7 4.2a3.1 3.1 0 0 1 3.1 3.1v.3a2.9 2.9 0 0 1 1.5 5 2.9 2.9 0 0 1-1.7 5 3.1 3.1 0 0 1-2.9 2.1h-.4V4.2Z" fill="currentColor" fill-opacity=".26"/>' +
    '<path d="M12 4.2v15.6" stroke="currentColor" stroke-width="1.3"/>' +
    '<circle cx="7.1" cy="9.7" r="1" fill="currentColor"/><circle cx="16.9" cy="9.7" r="1" fill="currentColor"/>' +
    '<circle cx="6.4" cy="14.3" r="1" fill="currentColor"/><circle cx="17.6" cy="14.3" r="1" fill="currentColor"/>',
  "cloud": '<path d="M7.3 18.6a4.1 4.1 0 0 1-.5-8.1 5.6 5.6 0 0 1 11-1.3A4.3 4.3 0 0 1 17 18.6Z" fill="currentColor" fill-opacity=".3"/>' +
    '<path d="M12 8.8v7M9.2 12.6 12 15.8l2.8-3.2" stroke="currentColor" stroke-width="1.9" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
  "shield": '<path d="M12 3.4 4.9 6v5.6c0 4.6 3 7.6 7.1 9 4.1-1.4 7.1-4.4 7.1-9V6Z" fill="currentColor" fill-opacity=".28"/>' +
    '<path d="m8.5 12.1 2.7 2.7 4.6-5" stroke="currentColor" stroke-width="1.9" fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
  "smartphone": '<rect x="6.3" y="2.2" width="11.4" height="19.6" rx="2.6" fill="currentColor" fill-opacity=".16"/>' +
    '<rect x="8.2" y="5.1" width="3.1" height="3.1" rx=".8" fill="currentColor"/>' +
    '<rect x="12.7" y="5.1" width="3.1" height="3.1" rx=".8" fill="currentColor"/>' +
    '<rect x="8.2" y="9.4" width="3.1" height="3.1" rx=".8" fill="currentColor"/>' +
    '<rect x="12.7" y="9.4" width="3.1" height="3.1" rx=".8" fill="currentColor"/>' +
    '<path d="M10.4 18.6h3.2" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/>',
  "palette": '<path d="M12 3.3a8.7 8.7 0 1 0 0 17.4c1.1 0 1.8-.9 1.8-1.8 0-.5-.2-1-.5-1.3a1.6 1.6 0 0 1 1.2-2.7h1.9a3.9 3.9 0 0 0 3.8-3.9c0-4.3-3.7-7.7-8.2-7.7Z" fill="currentColor" fill-opacity=".24"/>' +
    '<circle cx="7.3" cy="11.1" r="1.5" fill="currentColor"/><circle cx="9.5" cy="7.3" r="1.5" fill="currentColor"/>' +
    '<circle cx="14.7" cy="6.9" r="1.5" fill="currentColor"/><circle cx="16.8" cy="10.6" r="1.5" fill="currentColor"/>',
  "briefcase": '<rect x="3.2" y="8" width="17.6" height="11.2" rx="2" fill="currentColor" fill-opacity=".24"/>' +
    '<path d="M8.5 8V6a2.1 2.1 0 0 1 2.1-2.1h2.8A2.1 2.1 0 0 1 15.5 6v2" stroke="currentColor" stroke-width="1.7" fill="none"/>' +
    '<path d="M3.2 12.8h17.6M10.6 12.3v2.6M13.4 12.3v2.6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>',
  "server": '<rect x="3.6" y="4" width="16.8" height="6.4" rx="1.8" fill="currentColor" fill-opacity=".24"/>' +
    '<rect x="3.6" y="13.6" width="16.8" height="6.4" rx="1.8" fill="currentColor" fill-opacity=".24"/>' +
    '<circle cx="7.2" cy="7.2" r="1.1" fill="currentColor"/><circle cx="7.2" cy="16.8" r="1.1" fill="currentColor"/>' +
    '<path d="M11.2 7.2h6.4M11.2 16.8h6.4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>',
  "database": '<path d="M4.6 6v11.6c0 1.6 3.3 2.9 7.4 2.9s7.4-1.3 7.4-2.9V6" fill="currentColor" fill-opacity=".16" stroke="currentColor" stroke-width="1.3"/>' +
    '<path d="M4.6 11.8c0 1.6 3.3 2.9 7.4 2.9s7.4-1.3 7.4-2.9" stroke="currentColor" stroke-width="1.3" fill="none"/>' +
    '<ellipse cx="12" cy="6" rx="7.4" ry="2.7" fill="currentColor" fill-opacity=".32" stroke="currentColor" stroke-width="1.3"/>',
};

function bannerIconSvg(name, size) {
  size = size || 34;
  const inner = BANNER_ICONS[name] || BANNER_ICONS["code"];
  return '<svg width="' + size + '" height="' + size + '" viewBox="0 0 24 24" aria-hidden="true">' + inner + "</svg>";
}

const CATEGORY_META = {
  "Web Development": { icon: "code", c1: "#6366f1", c2: "#8b5cf6" },
  "Data Science": { icon: "bar-chart", c1: "#0ea5e9", c2: "#06b6d4" },
  "Machine Learning & AI": { icon: "cpu", c1: "#8b5cf6", c2: "#d946ef" },
  "Cloud Computing": { icon: "cloud", c1: "#38bdf8", c2: "#6366f1" },
  "Cybersecurity": { icon: "shield", c1: "#f43f5e", c2: "#fb7185" },
  "Mobile Development": { icon: "smartphone", c1: "#10b981", c2: "#34d399" },
  "UI/UX Design": { icon: "palette", c1: "#f97316", c2: "#fb923c" },
  "Business & Product Management": { icon: "briefcase", c1: "#d97706", c2: "#f59e0b" },
  "DevOps & SRE": { icon: "server", c1: "#64748b", c2: "#94a3b8" },
  "Databases & Data Engineering": { icon: "database", c1: "#14b8a6", c2: "#2dd4bf" },
};

const STATUS_LABELS = {
  saved: "Saved",
  known: "Already know this",
  in_progress: "In Progress",
  completed: "Completed",
};

function categoryMeta(category) {
  return CATEGORY_META[category] || { icon: "book-open", c1: "#6d28d9", c2: "#ec4899" };
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function showToast(message, isError) {
  const toast = document.getElementById("toast");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.toggle("error", !!isError);
  toast.classList.add("show");
  clearTimeout(showToast._t);
  showToast._t = setTimeout(function () { toast.classList.remove("show"); }, 3000);
}

function stars(rating) {
  return "★".repeat(Math.round(rating)) + "☆".repeat(5 - Math.round(rating));
}

// opts: { showMatch: bool, showStatus: bool }
function renderCourseCard(course, opts) {
  opts = opts || {};
  const meta = categoryMeta(course.category);
  const skillsHtml = (course.skills || []).slice(0, 3).map(function (s) {
    return '<span class="skill-chip">' + escapeHtml(s) + "</span>";
  }).join("");

  const badgeHtml = (opts.showMatch && course.match_pct !== null && course.match_pct !== undefined)
    ? '<span class="course-banner-badge">' + course.match_pct + "% Match</span>"
    : (opts.showMatch ? '<span class="course-banner-badge">Popular</span>' : "");

  const matchHtml = (opts.showMatch && course.match_pct !== null && course.match_pct !== undefined)
    ? '<span class="match-pill">' + course.match_pct + "% match</span>"
    : (opts.showMatch ? '<span class="match-pill neutral">Popular</span>' : "<span></span>");

  const whyHtml = (opts.showMatch && course.why)
    ? '<div class="why-line"><b>Matched on:</b> ' + escapeHtml(course.why) + "</div>"
    : "";

  const statusHtml = opts.showStatus
    ? '<select class="status-select ' + (course.status ? "is-set" : "") + '" data-course-id="' + course.course_id + '">' +
        '<option value="">+ Add</option>' +
        Object.keys(STATUS_LABELS).map(function (s) {
          return '<option value="' + s + '"' + (course.status === s ? " selected" : "") + '>' + STATUS_LABELS[s] + "</option>";
        }).join("") +
      "</select>"
    : "";

  return (
    '<div class="course-card" data-course-id="' + course.course_id + '">' +
      '<div class="course-banner" style="background:' + meta.c1 + ';">' +
        badgeHtml +
        '<span class="course-banner-level">' + escapeHtml(course.level) + "</span>" +
        '<span class="course-banner-icon-tile" style="color:' + meta.c1 + ';">' + bannerIconSvg(meta.icon, 32) + "</span>" +
      "</div>" +
      '<div class="course-body">' +
        '<div class="course-category">' + escapeHtml(course.category) + "</div>" +
        '<div class="course-title"><a href="/course/' + course.course_id + '">' + escapeHtml(course.title) + "</a></div>" +
        '<div class="course-meta"><span class="stars">' + stars(course.rating) + "</span><span>" + course.rating.toFixed(1) + "</span><span>&middot;</span><span>" + course.duration_hours + "h</span><span>&middot;</span><span>" + course.students.toLocaleString() + " students</span></div>" +
        '<div class="course-skills">' + skillsHtml + "</div>" +
        whyHtml +
        '<div class="course-footer">' + matchHtml + statusHtml + "</div>" +
      "</div>" +
    "</div>"
  );
}

// ---- sidebar: mobile toggle ----
(function () {
  const burger = document.getElementById("sidebar-burger");
  const sidebar = document.getElementById("sidebar");
  if (burger && sidebar) {
    burger.addEventListener("click", function (e) {
      e.stopPropagation();
      const open = sidebar.classList.toggle("open");
      burger.setAttribute("aria-expanded", open ? "true" : "false");
    });
    document.addEventListener("click", function (e) {
      if (sidebar.classList.contains("open") && !sidebar.contains(e.target) && e.target !== burger) {
        sidebar.classList.remove("open");
        burger.setAttribute("aria-expanded", "false");
      }
    });
  }
})();

// opts: { icon: bool } renders a slim row for the "Continue Learning" list
function renderContinueRow(course) {
  const meta = categoryMeta(course.category);
  const statusLabel = STATUS_LABELS[course.status] || course.status;
  return (
    '<div class="continue-item">' +
      '<div class="continue-icon" style="background:' + meta.c1 + ';">' + iconSvg(meta.icon, 16) + "</div>" +
      '<div class="continue-title-block">' +
        '<div class="continue-title"><a href="/course/' + course.course_id + '">' + escapeHtml(course.title) + "</a></div>" +
        '<div class="continue-meta">' + escapeHtml(course.category) + ' &middot; ' + course.duration_hours + "h</div>" +
      "</div>" +
      '<span class="status-pill ' + escapeHtml(course.status || "") + '">' + escapeHtml(statusLabel) + "</span>" +
    "</div>"
  );
}

// renders the "Explore by Category" icon grid from [{category, count}]
function renderCategoryGrid(categoryCounts, browseUrl) {
  return categoryCounts.map(function (row) {
    const meta = categoryMeta(row.category);
    return (
      '<a class="category-icon-card" href="' + browseUrl + "?category=" + encodeURIComponent(row.category) + '">' +
        '<div class="category-icon-badge" style="background:' + meta.c1 + ';">' + iconSvg(meta.icon, 18) + "</div>" +
        '<div><div class="category-icon-name">' + escapeHtml(row.category) + "</div>" +
        '<div class="category-icon-count">' + row.count + " course" + (row.count === 1 ? "" : "s") + "</div></div>" +
      "</a>"
    );
  }).join("");
}

function wireStatusSelects(container) {
  const section = container.getAttribute("data-section"); // set on My Learning's per-status grids
  container.querySelectorAll(".status-select").forEach(function (sel) {
    sel.addEventListener("change", function () {
      const courseId = sel.getAttribute("data-course-id");
      const status = sel.value || null;
      fetch("/api/my-learning/" + courseId, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: status }),
      })
        .then(function (res) { return res.json().then(function (b) { return { ok: res.ok, body: b }; }); })
        .then(function (r) {
          if (!r.ok) {
            showToast(r.body.message || "Could not update", true);
            return;
          }
          sel.classList.toggle("is-set", !!status);
          showToast(status ? "Added to My Learning" : "Removed");
          // On My Learning, a status change moves the course to a different
          // section and changes the stat counts at the top - simplest to
          // just reload rather than hand-patch every number on the page.
          if (section) {
            setTimeout(function () { window.location.reload(); }, 300);
          }
        })
        .catch(function (err) { showToast("Network error: " + err, true); });
    });
  });
}
