(function () {
  "use strict";

  // Category icon badge.
  const iconEl = document.getElementById("detail-icon");
  const meta = categoryMeta(iconEl.getAttribute("data-category"));
  iconEl.style.background = meta.c1;
  iconEl.textContent = meta.icon;

  // Single status dropdown - same control used everywhere else on the site.
  const statusSelect = document.getElementById("detail-status-select");
  statusSelect.addEventListener("change", function () {
    const courseId = statusSelect.getAttribute("data-course-id");
    const status = statusSelect.value || null;
    fetch("/api/my-learning/" + courseId, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: status }),
    })
      .then(function (res) { return res.json().then(function (b) { return { ok: res.ok, body: b }; }); })
      .then(function (r) {
        if (!r.ok) { showToast(r.body.message || "Could not update", true); return; }
        statusSelect.classList.toggle("is-set", !!status);
        showToast(status ? "Updated" : "Removed from My Learning");
      })
      .catch(function (err) { showToast("Network error: " + err, true); });
  });

  // Similar courses grid.
  const similar = JSON.parse(document.getElementById("similar-courses").textContent);
  const grid = document.getElementById("similar-grid");
  if (!similar.length) {
    grid.innerHTML = '<div class="empty-note">No close matches found yet.</div>';
  } else {
    grid.innerHTML = similar.map(function (c) { return renderCourseCard(c, { showMatch: true, showStatus: true }); }).join("");
    wireStatusSelects(grid);
  }

  // Review form: star picker + submit.
  const starInput = document.getElementById("review-star-input");
  const starSpans = starInput ? starInput.querySelectorAll("span") : [];
  let selectedRating = 0;
  function paintStars(n) {
    starSpans.forEach(function (s) {
      s.classList.toggle("active", parseInt(s.getAttribute("data-value"), 10) <= n);
    });
  }
  starSpans.forEach(function (s) {
    s.addEventListener("mouseenter", function () { paintStars(parseInt(s.getAttribute("data-value"), 10)); });
    s.addEventListener("click", function () {
      selectedRating = parseInt(s.getAttribute("data-value"), 10);
      paintStars(selectedRating);
    });
  });
  if (starInput) {
    starInput.addEventListener("mouseleave", function () { paintStars(selectedRating); });
  }

  const commentInput = document.getElementById("review-comment-input");
  const submitBtn = document.getElementById("review-submit-btn");
  const reviewNote = document.getElementById("review-note");
  const reviewList = document.getElementById("review-list");

  if (submitBtn) {
    submitBtn.addEventListener("click", function () {
      const comment = commentInput.value.trim();
      if (!selectedRating) {
        reviewNote.textContent = "Pick a star rating first.";
        reviewNote.style.color = "var(--accent)";
        return;
      }
      if (!comment) {
        reviewNote.textContent = "Write a short comment first.";
        reviewNote.style.color = "var(--accent)";
        return;
      }
      submitBtn.disabled = true;
      submitBtn.textContent = "Posting…";
      fetch("/api/courses/" + window.COURSE_ID + "/reviews", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rating: selectedRating, comment: comment, reviewer_name: window.PROFILE_NAME }),
      })
        .then(function (res) { return res.json().then(function (b) { return { ok: res.ok, body: b }; }); })
        .then(function (r) {
          submitBtn.disabled = false;
          submitBtn.textContent = "Post Review";
          if (!r.ok) {
            reviewNote.textContent = r.body.message || "Something went wrong.";
            reviewNote.style.color = "var(--accent)";
            return;
          }
          reviewNote.textContent = "";
          const emptyNote = reviewList.querySelector(".empty-note");
          if (emptyNote) emptyNote.remove();
          const name = window.PROFILE_NAME || "Anonymous";
          const item = document.createElement("div");
          item.className = "review-item";
          item.innerHTML =
            '<div class="review-head">' +
              '<span class="review-avatar">' + escapeHtml(name.slice(0, 1).toUpperCase()) + "</span>" +
              '<span class="review-name">' + escapeHtml(name) + "</span>" +
              '<span class="review-stars">' + "★".repeat(selectedRating) + "☆".repeat(5 - selectedRating) + "</span>" +
              '<span class="review-date">' + new Date().toISOString().slice(0, 10) + "</span>" +
            "</div>" +
            '<p class="review-comment">' + escapeHtml(comment) + "</p>";
          reviewList.insertBefore(item, reviewList.firstChild);
          commentInput.value = "";
          selectedRating = 0;
          paintStars(0);
          const titleEl = document.getElementById("review-count-title");
          if (titleEl) {
            const n = reviewList.querySelectorAll(".review-item").length;
            titleEl.textContent = "Learner Reviews on CourseCompass (" + n + ")";
          }
          showToast("Review posted");
        })
        .catch(function (err) {
          submitBtn.disabled = false;
          submitBtn.textContent = "Post Review";
          showToast("Network error: " + err, true);
        });
    });
  }
})();
