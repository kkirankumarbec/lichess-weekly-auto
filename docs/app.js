(function () {
  "use strict";

  var PIECE_UNICODE = {
    wK: "♔", wQ: "♕", wR: "♖", wB: "♗", wN: "♘", wP: "♙",
    bK: "♚", bQ: "♛", bR: "♜", bB: "♝", bN: "♞", bP: "♟"
  };
  var FILES = "abcdefgh";

  var boardEl = document.getElementById("board");
  var statusEl = document.getElementById("status");
  var metaEl = document.getElementById("puzzle-meta");
  var linkEl = document.getElementById("puzzle-link");
  var nameCard = document.getElementById("name-card");
  var nameInput = document.getElementById("name-input");
  var saveBtn = document.getElementById("save-btn");
  var saveStatus = document.getElementById("save-status");
  var resetBtn = document.getElementById("reset-btn");

  var state = {
    puzzle: null,
    game: null,
    orientation: "white",
    solutionIndex: 0,
    selected: null,
    legalTargets: [],
    lastMove: null,
    solved: false,
    locked: false
  };

  function squareAt(row, col) {
    var fileIndex, rankNumber;
    if (state.orientation === "white") {
      fileIndex = col;
      rankNumber = 8 - row;
    } else {
      fileIndex = 7 - col;
      rankNumber = row + 1;
    }
    return FILES[fileIndex] + rankNumber;
  }

  function setStatus(text, cls) {
    statusEl.textContent = text || "";
    statusEl.className = cls || "";
  }

  function renderBoard() {
    boardEl.innerHTML = "";
    for (var row = 0; row < 8; row++) {
      for (var col = 0; col < 8; col++) {
        var sq = squareAt(row, col);
        var div = document.createElement("div");
        var isLight = (row + col) % 2 === 0;
        div.className = "square " + (isLight ? "light" : "dark");
        if (state.selected === sq) div.classList.add("selected");
        if (state.legalTargets.indexOf(sq) !== -1) div.classList.add("legal");
        if (state.lastMove && (state.lastMove.from === sq || state.lastMove.to === sq)) {
          div.classList.add("lastmove");
        }
        var piece = state.game.get(sq);
        if (piece) {
          div.textContent = PIECE_UNICODE[piece.color + piece.type.toUpperCase()];
        }
        div.dataset.square = sq;
        div.addEventListener("click", onSquareClick);
        boardEl.appendChild(div);
      }
    }
  }

  function expectedPromotion(from, to) {
    var expected = state.puzzle.solution[state.solutionIndex];
    if (expected && expected.length === 5 && expected.slice(0, 2) === from && expected.slice(2, 4) === to) {
      return expected[4];
    }
    return "q";
  }

  function onSquareClick(e) {
    if (state.solved || state.locked) return;
    var sq = e.currentTarget.dataset.square;
    var piece = state.game.get(sq);
    var turnColor = state.game.turn();

    if (!state.selected) {
      if (piece && piece.color === turnColor) selectSquare(sq);
      return;
    }

    if (sq === state.selected) {
      clearSelection();
      renderBoard();
      return;
    }

    if (state.legalTargets.indexOf(sq) !== -1) {
      var promotion = expectedPromotion(state.selected, sq);
      var moved = state.game.move({ from: state.selected, to: sq, promotion: promotion });
      clearSelection();
      if (moved) handleUserMove(moved);
      else renderBoard();
      return;
    }

    if (piece && piece.color === turnColor) {
      selectSquare(sq);
      return;
    }

    clearSelection();
    renderBoard();
  }

  function selectSquare(sq) {
    state.selected = sq;
    var moves = state.game.moves({ square: sq, verbose: true });
    state.legalTargets = moves.map(function (m) { return m.to; });
    renderBoard();
  }

  function clearSelection() {
    state.selected = null;
    state.legalTargets = [];
  }

  function handleUserMove(moved) {
    var uci = moved.from + moved.to + (moved.promotion || "");
    var expected = state.puzzle.solution[state.solutionIndex];

    if (uci !== expected) {
      state.game.undo();
      state.lastMove = null;
      setStatus("Not quite - try again!", "bad");
      renderBoard();
      return;
    }

    state.solutionIndex++;
    state.lastMove = { from: moved.from, to: moved.to };
    setStatus("Correct!", "ok");
    renderBoard();

    if (state.solutionIndex >= state.puzzle.solution.length) {
      onSolved();
      return;
    }

    state.locked = true;
    setTimeout(function () {
      var replyUci = state.puzzle.solution[state.solutionIndex];
      playUci(replyUci);
      state.solutionIndex++;
      state.locked = false;
      renderBoard();
      if (state.solutionIndex >= state.puzzle.solution.length) onSolved();
      else setStatus("Your move...", "");
    }, 500);
  }

  function playUci(uci) {
    var from = uci.slice(0, 2);
    var to = uci.slice(2, 4);
    var promotion = uci.length > 4 ? uci.slice(4) : undefined;
    var moved = state.game.move({ from: from, to: to, promotion: promotion });
    if (moved) state.lastMove = { from: moved.from, to: moved.to };
  }

  function onSolved() {
    state.solved = true;
    setStatus("Solved! Great job! 🎉", "ok");
    var week = state.puzzle.week;
    var savedName = localStorage.getItem("kcc-puzzle-saved-" + week);
    if (savedName) {
      nameCard.classList.add("hidden");
      saveStatus.textContent = "Already saved as " + savedName + " for this week.";
    } else if (!window.PUZZLE_CONFIG.formActionUrl) {
      nameCard.classList.remove("hidden");
      nameInput.disabled = true;
      saveBtn.disabled = true;
      saveStatus.textContent = "Scoring isn't wired up yet - ask your coach!";
    } else {
      nameCard.classList.remove("hidden");
      nameInput.focus();
    }
  }

  function initPuzzle(puzzle) {
    state.puzzle = puzzle;
    state.game = new Chess(puzzle.fen);
    state.orientation = puzzle.sideToMove;
    state.solutionIndex = 0;
    state.selected = null;
    state.legalTargets = [];
    state.lastMove = null;
    state.solved = false;
    state.locked = false;
    setStatus("Your move - " + puzzle.sideToMove + " to play.", "");
    nameCard.classList.add("hidden");
    saveStatus.textContent = "";
    renderBoard();

    metaEl.textContent =
      "Week " + puzzle.week + " · Rating ~" + puzzle.rating +
      (puzzle.themes && puzzle.themes.length ? " · " + puzzle.themes.slice(0, 2).join(", ") : "");
    linkEl.innerHTML = puzzle.lichessUrl
      ? '<a href="' + puzzle.lichessUrl + '" target="_blank" rel="noopener">View this puzzle on Lichess</a>'
      : "";
  }

  resetBtn.addEventListener("click", function () {
    if (state.puzzle) initPuzzle(state.puzzle);
  });

  saveBtn.addEventListener("click", function () {
    var name = (nameInput.value || "").trim();
    if (!name) {
      saveStatus.textContent = "Please type your name first.";
      return;
    }
    var cfg = window.PUZZLE_CONFIG;
    var body = new URLSearchParams();
    body.set(cfg.formEntryName, name);
    body.set(cfg.formEntryWeek, state.puzzle.week);

    saveBtn.disabled = true;
    fetch(cfg.formActionUrl, {
      method: "POST",
      mode: "no-cors",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString()
    }).catch(function () {
      // no-cors gives no readable response either way; this just catches
      // a hard network failure (offline, blocked), not a form rejection.
    }).then(function () {
      localStorage.setItem("kcc-puzzle-saved-" + state.puzzle.week, name);
      saveStatus.textContent = "Saved! See you on the leaderboard soon.";
    });
  });

  // ---- Leaderboard ----

  var activeTab = "week";
  var leaderboardData = null;

  function renderLeaderboard() {
    var tbody = document.querySelector("#leaderboard-table tbody");
    tbody.innerHTML = "";
    if (!leaderboardData) return;
    var rows = activeTab === "week" ? leaderboardData.thisWeek : leaderboardData.allTime;
    if (!rows || !rows.length) {
      tbody.innerHTML = '<tr><td colspan="2">No scores yet - be the first!</td></tr>';
    } else {
      rows.forEach(function (r) {
        var tr = document.createElement("tr");
        tr.innerHTML = "<td>" + escapeHtml(r.name) + "</td><td>" + r.points + "</td>";
        tbody.appendChild(tr);
      });
    }
    document.getElementById("leaderboard-meta").textContent = leaderboardData.updatedAtUtc
      ? "Updated " + leaderboardData.updatedAtUtc + " UTC"
      : "";
  }

  function escapeHtml(s) {
    var div = document.createElement("div");
    div.textContent = s;
    return div.innerHTML;
  }

  document.querySelectorAll(".tab").forEach(function (tab) {
    tab.addEventListener("click", function () {
      document.querySelectorAll(".tab").forEach(function (t) { t.classList.remove("active"); });
      tab.classList.add("active");
      activeTab = tab.dataset.tab;
      renderLeaderboard();
    });
  });

  // ---- Load data ----

  fetch("puzzle.json?t=" + Date.now(), { cache: "no-store" })
    .then(function (r) { return r.json(); })
    .then(initPuzzle)
    .catch(function () {
      metaEl.textContent = "Couldn't load this week's puzzle - ask your coach to check.";
    });

  fetch("leaderboard.json?t=" + Date.now(), { cache: "no-store" })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      leaderboardData = data;
      renderLeaderboard();
    })
    .catch(function () {
      document.getElementById("leaderboard-meta").textContent = "Leaderboard not available yet.";
    });
})();
