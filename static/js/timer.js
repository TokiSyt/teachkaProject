/**
 * Shared timer utilities for stopwatch and countdown.
 */

const ITEM_H = 40;

/* ── Time formatting ── */

function formatTime(ms) {
  const totalSeconds = Math.floor(ms / 1000);
  const h = Math.floor(totalSeconds / 3600);
  const m = String(Math.floor((totalSeconds % 3600) / 60)).padStart(2, "0");
  const s = String(totalSeconds % 60).padStart(2, "0");
  const cs = String(Math.floor((ms % 1000) / 10)).padStart(2, "0");
  const main = h > 0 ? String(h).padStart(2, "0") + ":" + m + ":" + s : m + ":" + s;
  return { main, cs };
}

function updateTimerDisplay(mainEl, msEl, ms) {
  const t = formatTime(ms);
  const showHours = ms >= 3600000;
  const current = mainEl.dataset.hours === "1";

  if (showHours !== current) {
    mainEl.dataset.hours = showHours ? "1" : "0";
    mainEl.classList.toggle("text-5xl", !showHours);
    mainEl.classList.toggle("sm:text-6xl", !showHours);
    mainEl.classList.toggle("text-4xl", showHours);
    mainEl.classList.toggle("sm:text-5xl", showHours);
    msEl.classList.toggle("text-xl", !showHours);
    msEl.classList.toggle("sm:text-2xl", !showHours);
    msEl.classList.toggle("text-lg", showHours);
    msEl.classList.toggle("sm:text-xl", showHours);
  }

  mainEl.textContent = t.main;
  msEl.textContent = "." + t.cs;
}

/* ── Button visibility helper ── */

function showButtons(allBtns, ...visible) {
  allBtns.forEach(b => b.classList.add("hidden"));
  visible.forEach(b => b.classList.remove("hidden"));
}

/* ── Scroll picker (countdown) ── */

function initPicker(container, max, initial) {
  const count = max + 1;

  for (let r = 0; r < 3; r++) {
    for (let i = 0; i <= max; i++) {
      const item = document.createElement("div");
      item.className = "scroll-picker-item flex items-center justify-center text-2xl font-mono font-bold text-gray-900 dark:text-white";
      item.textContent = String(i).padStart(2, "0");
      container.appendChild(item);
    }
  }

  const spacer = document.createElement("div");
  spacer.className = "scroll-picker-item";
  container.appendChild(spacer);

  container.scrollTop = (count + initial) * ITEM_H;

  // Loop: jump to middle copy when reaching edges
  let scrollTimeout;
  container.addEventListener("scroll", function () {
    clearTimeout(scrollTimeout);
    scrollTimeout = setTimeout(function () {
      const index = Math.round(container.scrollTop / ITEM_H);
      const value = index % count;
      if (index < count || index >= count * 2) {
        container.scrollTop = (count + value) * ITEM_H;
      }
    }, 100);
  });

  // Desktop drag-to-scroll
  let dragging = false, startY = 0, startScroll = 0;

  container.addEventListener("mousedown", function (e) {
    dragging = true;
    startY = e.clientY;
    startScroll = container.scrollTop;
    e.preventDefault();
  });

  window.addEventListener("mousemove", function (e) {
    if (!dragging) return;
    container.scrollTop = startScroll + (startY - e.clientY);
  });

  window.addEventListener("mouseup", function () {
    dragging = false;
  });
}

function getPickerValue(container, max) {
  const index = Math.round(container.scrollTop / ITEM_H);
  return index % (max + 1);
}

/* ── Usage tracking ── */

function track(action, elapsed) {
  const data = new URLSearchParams({ action: action });
  if (elapsed !== undefined) data.append("elapsed", String(Math.floor(elapsed)));
  fetch("", { method: "POST", headers: { "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value }, body: data });
}
