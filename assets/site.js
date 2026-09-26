(function () {
  "use strict";

  var yearEl = document.getElementById("year");
  if (yearEl) {
    yearEl.textContent = String(new Date().getFullYear());
  }

  // Keyboard: j/k or ArrowDown/ArrowUp moves focus between the play links
  var links = Array.prototype.slice.call(
    document.querySelectorAll(".trk-play")
  );
  if (!links.length) return;

  document.addEventListener("keydown", function (e) {
    if (e.altKey || e.ctrlKey || e.metaKey) return;
    var tag = (e.target && e.target.tagName) || "";
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;

    var key = e.key;
    var down = key === "j" || key === "ArrowDown";
    var up = key === "k" || key === "ArrowUp";
    if (!down && !up) return;

    var idx = links.indexOf(document.activeElement);
    var next;
    if (idx === -1) {
      next = down ? 0 : links.length - 1;
    } else {
      next = down ? Math.min(idx + 1, links.length - 1) : Math.max(idx - 1, 0);
    }
    if (next !== idx) {
      links[next].focus();
      links[next].scrollIntoView({ block: "nearest" });
      e.preventDefault();
    }
  });
})();
