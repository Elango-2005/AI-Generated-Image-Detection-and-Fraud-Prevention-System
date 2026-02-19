const uploadInput = document.getElementById("upload");
const dropZone = document.getElementById("drop-zone");
const previewImage = document.getElementById("preview-image");
const uploadIcon = document.getElementById("upload-icon");
const fileName = document.getElementById("file-name");
const form = document.querySelector(".upload-form");
const statusMsg = document.getElementById("statusMsg");
const submitBtn = form.querySelector("button");

const historySidebar = document.getElementById("history-sidebar");
const historyToggle = document.getElementById("history-toggle");
const closeHistory = document.getElementById("close-history");
const historyList = document.getElementById("history-list");
const imageCount = document.getElementById("image-count");

const searchInput = document.getElementById("search-history");
const clearSearchBtn = document.getElementById("clear-search");
const clearHistoryBtn = document.getElementById("clear-history");

const overlay = document.getElementById("overlay");
const themeToggle = document.getElementById("theme-toggle");
const postsBtn = document.getElementById("posts-btn");

document.addEventListener("DOMContentLoaded", loadHistory);

////////////////////////////////////////////////////////////
// SIDEBAR
////////////////////////////////////////////////////////////

historyToggle.addEventListener("click", () => {
  historySidebar.classList.add("active");
  overlay.classList.add("active");
});

closeHistory.addEventListener("click", closeSidebar);
overlay.addEventListener("click", closeSidebar);

function closeSidebar() {
  historySidebar.classList.remove("active");
  overlay.classList.remove("active");
}

////////////////////////////////////////////////////////////
// POSTS BUTTON (Flask route)
////////////////////////////////////////////////////////////

postsBtn.addEventListener("click", () => {
  window.location.href = "/posts";
});

////////////////////////////////////////////////////////////
// IMAGE PREVIEW
////////////////////////////////////////////////////////////

dropZone.addEventListener("click", () => {
  if (historySidebar.classList.contains("active")) return;
  uploadInput.click();
});

uploadInput.addEventListener("change", () => {

  const file = uploadInput.files[0];

  if (!file || !file.type.startsWith("image/")) return;

  const reader = new FileReader();

  reader.onload = e => {

    previewImage.src = e.target.result;
    previewImage.style.display = "block";

    uploadIcon.style.display = "none";

    fileName.textContent = file.name;
  };

  reader.readAsDataURL(file);
});

////////////////////////////////////////////////////////////
// UPLOAD + BACKEND CALL (FULL PROTECTION VERSION)
////////////////////////////////////////////////////////////

form.addEventListener("submit", async function (e) {

  e.preventDefault();

  if (!uploadInput.files.length) return;

  const file = uploadInput.files[0];

  const formData = new FormData();
  formData.append("file", file);

  try {

    ////////////////////////////////////////////////////////////
    // Prevent double submit
    ////////////////////////////////////////////////////////////

    submitBtn.disabled = true;

    ////////////////////////////////////////////////////////////
    // Show loading
    ////////////////////////////////////////////////////////////

    statusMsg.className = "status loading";
    statusMsg.innerHTML = "Analyzing image...";

    ////////////////////////////////////////////////////////////
    // Network timeout protection
    ////////////////////////////////////////////////////////////

    const controller = new AbortController();

    const timeout = setTimeout(() => {
      controller.abort();
    }, 15000);

    const response = await fetch("/predict", {
      method: "POST",
      body: formData,
      signal: controller.signal
    });

    clearTimeout(timeout);

    if (!response.ok)
      throw new Error("Server error");

    const result = await response.json();

    const decision = result.decision;
    const confidence = result.confidence;
    const allowed = result.allowed;
    const message = result.message;

    ////////////////////////////////////////////////////////////
    // BLOCKED IMAGE (FAKE OR SUSPICIOUS)
    ////////////////////////////////////////////////////////////

    if (!allowed) {

      if (decision === "SUSPICIOUS") {

        statusMsg.className = "status suspicious";

        statusMsg.innerHTML = `
          ⚠ Under Human Review<br>
          Confidence: ${confidence}%
        `;
      }

      else {

        statusMsg.className = "status error";

        statusMsg.innerHTML = `
          ${message}<br>
          Confidence: ${confidence}%
        `;
      }

      resetUploadUI();

      submitBtn.disabled = false;

      return;
    }

    ////////////////////////////////////////////////////////////
    // ALLOWED IMAGE (REAL)
    ////////////////////////////////////////////////////////////

    statusMsg.className = "status real";

    statusMsg.innerHTML = `
      ${message}<br>
      Confidence: ${confidence}%
    `;

    saveToHistory(file, decision, confidence);

    resetUploadUI();

    submitBtn.disabled = false;

  }

  catch (error) {

    submitBtn.disabled = false;

    if (error.name === "AbortError") {

      statusMsg.className = "status error";

      statusMsg.innerHTML = "Request timeout. Try again.";
    }

    else {

      statusMsg.className = "status error";

      statusMsg.innerHTML = "Error connecting to backend.";
    }

    console.error(error);
  }
});

////////////////////////////////////////////////////////////
// RESET UPLOAD UI
////////////////////////////////////////////////////////////

function resetUploadUI() {

  uploadInput.value = "";

  previewImage.style.display = "none";

  uploadIcon.style.display = "block";

  fileName.textContent = "Click or Drag & Drop image";
}

////////////////////////////////////////////////////////////
// SAVE HISTORY (REAL ONLY)
////////////////////////////////////////////////////////////

function saveToHistory(file, decision, confidence) {

  const reader = new FileReader();

  reader.onload = e => {

    const imageData = e.target.result;

    let history =
      JSON.parse(localStorage.getItem("imageHistory")) || [];

    history.unshift({
      id: Date.now(),
      name: file.name,
      data: imageData,
      decision: decision,
      confidence: confidence
    });

    localStorage.setItem(
      "imageHistory",
      JSON.stringify(history)
    );

    loadHistory();
  };

  reader.readAsDataURL(file);
}

////////////////////////////////////////////////////////////
// LOAD HISTORY
////////////////////////////////////////////////////////////

function loadHistory() {

  const history =
    JSON.parse(localStorage.getItem("imageHistory")) || [];

  historyList.innerHTML = "";

  imageCount.textContent = history.length;

  if (!history.length) {

    historyList.innerHTML = "<p>EMPTY</p>";

    return;
  }

  history.forEach((item, index) => {

    const div = document.createElement("div");

    div.className =
      "mb-2 p-2 bg-light rounded d-flex justify-content-between align-items-center";

    const name = document.createElement("span");

    name.textContent =
      `${item.name} (${item.confidence}%)`;

    name.style.cursor = "pointer";

    const del = document.createElement("button");

    del.className = "btn btn-sm btn-danger";

    del.textContent = "🗑";

    del.onclick = (e) => {

      e.stopPropagation();

      history.splice(index, 1);

      localStorage.setItem(
        "imageHistory",
        JSON.stringify(history)
      );

      loadHistory();
    };

    div.appendChild(name);
    div.appendChild(del);

    historyList.appendChild(div);
  });
}

////////////////////////////////////////////////////////////
// SEARCH
////////////////////////////////////////////////////////////

searchInput.addEventListener("input", () => {

  const value = searchInput.value.toLowerCase();

  clearSearchBtn.style.display = value ? "block" : "none";

  document.querySelectorAll("#history-list div")
    .forEach(item => {

      item.style.display =
        item.textContent.toLowerCase().includes(value)
        ? "flex"
        : "none";
    });
});

clearSearchBtn.addEventListener("click", () => {

  searchInput.value = "";

  clearSearchBtn.style.display = "none";

  loadHistory();
});

////////////////////////////////////////////////////////////
// CLEAR HISTORY
////////////////////////////////////////////////////////////

clearHistoryBtn.addEventListener("click", () => {

  localStorage.setItem(
    "imageHistory",
    JSON.stringify([])
  );

  loadHistory();
});

////////////////////////////////////////////////////////////
// DARK MODE
////////////////////////////////////////////////////////////

themeToggle.addEventListener("click", () => {
  document.body.classList.toggle("dark-mode");
});
