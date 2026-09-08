// Ticking a session posts to the server, so the phone and the Mac agree.
(function () {
  "use strict";

  function post(url, body) {
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    });
  }

  function paintTotal(completed) {
    var count = document.getElementById("done-count");
    var fill = document.getElementById("progress-fill");
    if (!count || !fill) return;
    var total = Number(fill.dataset.total) || 0;
    count.textContent = completed;
    fill.style.width = total ? (completed / total) * 100 + "%" : "0%";
  }

  var section = document.querySelector(".progress");
  var slug = section ? section.dataset.slug : null;

  // Program page: one button per session.
  document.querySelectorAll(".check").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var next = btn.getAttribute("aria-checked") !== "true";
      btn.disabled = true;
      post("/api/progress", {
        slug: slug,
        week: Number(btn.dataset.week),
        day: Number(btn.dataset.day),
        done: next,
      })
        .then(function (data) {
          btn.setAttribute("aria-checked", next ? "true" : "false");
          btn.closest(".row").classList.toggle("is-done", next);
          paintTotal(data.completed);
        })
        .catch(function () {
          btn.classList.add("failed");   // stays unticked: the server said no
          setTimeout(function () { btn.classList.remove("failed"); }, 1200);
        })
        .then(function () { btn.disabled = false; });
    });
  });

  // Day page: one big button.
  var big = document.getElementById("done-btn");
  if (big) {
    big.addEventListener("click", function () {
      var next = big.getAttribute("aria-pressed") !== "true";
      big.disabled = true;
      post("/api/progress", {
        slug: big.dataset.slug,
        week: Number(big.dataset.week),
        day: Number(big.dataset.day),
        done: next,
      })
        .then(function () {
          big.setAttribute("aria-pressed", next ? "true" : "false");
          big.classList.toggle("is-done", next);
          big.querySelector(".label").textContent = next ? "Completed" : "Mark as done";
        })
        .catch(function () {
          big.classList.add("failed");
          setTimeout(function () { big.classList.remove("failed"); }, 1200);
        })
        .then(function () { big.disabled = false; });
    });
  }

  // Two taps, both drawn in the page. A native confirm() can be suppressed
  // by the browser and comes back as "cancel", which reads as a dead button.
  var reset = document.querySelector(".reset");
  if (reset && slug) {
    var armed = false;
    var timer = null;

    function disarm() {
      armed = false;
      clearTimeout(timer);
      reset.textContent = "Reset";
      reset.classList.remove("armed");
    }

    reset.addEventListener("click", function () {
      if (!armed) {
        armed = true;
        reset.textContent = "Tap again to clear";
        reset.classList.add("armed");
        timer = setTimeout(disarm, 4000);
        return;
      }
      disarm();
      reset.disabled = true;
      post("/api/progress/" + encodeURIComponent(slug) + "/reset", {})
        .then(function () { location.reload(); })
        .catch(function () {
          reset.disabled = false;
          reset.textContent = "Failed — try again";
        });
    });
  }
})();
