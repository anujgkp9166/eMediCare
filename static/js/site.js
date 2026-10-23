(function () {
  // mobile menu
  var toggle = document.querySelector("[data-nav-toggle]");
  var nav = document.querySelector("[data-nav]");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // auto-hide messages
  document.querySelectorAll(".msg").forEach(function (m) {
    setTimeout(function () { m.style.display = "none"; }, 7000);
  });

  // appointment booking: load free times for chosen doctor + date
  var form = document.querySelector("[data-slots-url]");
  if (form) {
    var doctor = form.querySelector("#id_doctor");
    var day = form.querySelector("#id_date");
    var select = form.querySelector("#id_slot");
    var hint = document.getElementById("slot-hint");
    var selected = select.getAttribute("data-selected") || "";

    var load = function () {
      if (!doctor.value || !day.value) { return; }
      select.disabled = true;
      hint.textContent = "Checking available times…";
      var url = form.getAttribute("data-slots-url") + "?doctor=" + encodeURIComponent(doctor.value) + "&date=" + encodeURIComponent(day.value);
      fetch(url, { headers: { "Accept": "application/json" } })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          select.innerHTML = "";
          if (!d.slots.length) {
            select.add(new Option("No times available", ""));
            hint.textContent = d.message || "Please choose another date.";
          } else {
            select.add(new Option("Choose a time", ""));
            d.slots.forEach(function (s) {
              var o = new Option(s.label, s.value);
              if (s.value === selected) { o.selected = true; }
              select.add(o);
            });
            hint.textContent = d.slots.length + " time(s) available";
          }
          select.disabled = false;
        })
        .catch(function () {
          hint.textContent = "Could not load times. Please try again.";
          select.disabled = false;
        });
    };
    doctor.addEventListener("change", function () { selected = ""; load(); });
    day.addEventListener("change", function () { selected = ""; load(); });
    load();
  }

  // test request: show address only for home collection
  var type = document.getElementById("id_collection_type");
  var addr = document.getElementById("id_address");
  if (type && addr) {
    var wrap = addr.closest(".field");
    var sync = function () { wrap.style.display = type.value === "home" ? "" : "none"; };
    type.addEventListener("change", sync);
    sync();
  }
})();
