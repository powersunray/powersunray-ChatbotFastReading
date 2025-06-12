document.addEventListener("DOMContentLoaded", function () {
  // DOM Elements
  const sessionList = document.querySelector(".document-groups");
  const groupContextMenu = document.querySelector(".group-context-menu");
  const itemContextMenu = document.querySelector(".item-context-menu");
  const fileList = document.querySelector(".file-list");
  const linkList = document.querySelector(".link-list");
  const chatMessages = document.getElementById("chatMessages");
  const chatInput = document.getElementById("chatInput");
  const sendBtn = document.getElementById("sendBtn");
  const addSessionBtn = document.querySelector(".add-group-btn");
  const uploadFileBtn = document.querySelector(".upload-file-btn");
  const fileUpload = document.getElementById("fileUpload");
  const addLinkBtn = document.querySelector(".add-link-btn");

  // Bootstrap Modals
  const groupModal = new bootstrap.Modal(document.getElementById("groupModal"));
  const linkModal = new bootstrap.Modal(document.getElementById("linkModal"));
  const renameModal = new bootstrap.Modal(document.getElementById("renameModal"));

  // State Variables
  let currentSessionId = null;
  let currentContextTarget = null;

  // 6 default groups
  const defaultGroups = [
    "Compliance",
    "Hardware Management",
    "Operations",
    "Risk",
    "Software Development",
    "Vendor Management",
  ];

  // Initialization
  async function init() {
    await loadSessions();
    addEventListeners();
    if (currentSessionId) {
      await loadSessionData(currentSessionId);
    }
  }

  // Load chat sessions & Check default initialization
  async function loadSessions() {
    try {
      const res = await fetch("http://127.0.0.1:5000/sessions");
      if (!res.ok) throw new Error("Failed to fetch sessions");
      let sessions = await res.json();
      console.log("Sessions fetched:", sessions);

      // If there is no session, create the 6 default groups
      if (sessions.length === 0) {
        console.log("No sessions found, creating default groups...");
        for (const name of defaultGroups) {
          await fetch("http://127.0.0.1:5000/sessions", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name }),
          });
        }
        // Call again to get the new list
        const newRes = await fetch("http://127.0.0.1:5000/sessions");
        sessions = await newRes.json();
        console.log("New sessions created:", sessions);
      }

      // Sorting sessions alphabetically
      sessions.sort((a, b) => a.name.localeCompare(b.name));

      // Render sorted list
      renderSessions(sessions);

      // Choose the first group if no group is selected
      if (!currentSessionId && sessions.length > 0) {
        currentSessionId = sessions[0].id;
        const firstItem = sessionList.querySelector(".list-group-item");
        firstItem.classList.add("active");
        await loadSessionData(currentSessionId);
      }
    } catch (error) {
      console.error("Error loading sessions:", error);
      alert("Failed to load sessions. Please try again.");
    }
  }

  function renderSessions(sessions) {
    sessionList.innerHTML = "";
    sessions.forEach(session => {
      const li = document.createElement("li");
      li.className = "list-group-item d-flex justify-content-between align-items-center";
      li.dataset.sessionId = session.id;
      li.textContent = session.name;
      const icon = document.createElement("i");
      icon.className = "fas fa-ellipsis-v group-menu-trigger";
      li.appendChild(icon);
      sessionList.appendChild(li);
    });
  }

  // Load files, links, chats for a session
  async function loadSessionData(sessionId) {
    try {
      currentSessionId = sessionId;
      // const res = await fetch(`/sessions/${sessionId}/assets`); //! assets or uploads?
      // Get files
      const filesRes = await fetch(`http://127.0.0.1:5000/sessions/${sessionId}/files`);
      if (!filesRes.ok) throw new Error("Failed to fetch files");
      const files = await filesRes.json();

      // Get links
      const linksRes = await fetch(`http://127.0.0.1:5000/sessions/${sessionId}/links`);
      if (!linksRes.ok) throw new Error("Failed to fetch links");
      const links = await linksRes.json();

      // Get chat history
      const chatsRes = await fetch(`http://127.0.0.1:5000/chat_history/${sessionId}`);
      if (!chatsRes.ok) throw new Error("Failed to fetch session data");
      const chats = await chatsRes.json();

      renderFiles(files);
      renderLinks(links);
      renderChatHistory(chats);
    } catch (error) {
      console.error("Error loading session data:", error);
      alert("Failed to load session data. Please try again.");
    }
  }

  function renderFiles(files) {
    if (!currentSessionId) return;
    fileList.innerHTML = files.length
      ? files
        .map(
          (f) => `
        <div class="file-item d-flex align-items-center" data-id="${f.id}">
          <div class="file-icon"><i class="fas fa-file"></i></div>
          <div class="file-name">${f.filename}</div>
          <div class="file-checkbox"><input type="checkbox" class="form-check-input"></div>
        </div>`
        )
        .join("")
    : '<p class="text-muted text-center">No files</p>';
  }

  function renderLinks(links) {
    if (!currentSessionId) return;
    linkList.innerHTML = links.length
      ? links
      .map(
        (l) => `
      <div class="link-item d-flex align-items-center" data-id="${l.id}">
        <div class="link-icon"><i class="fas fa-link"></i></div>
        <div class="link-name">${l.url}</div>
        <div class="link-checkbox"><input type="checkbox" class="form-check-input"></div>
      </div>`)
      .join("")
    : '<p class="text-muted text-center">No links</p>';
  }

  function renderChatHistory(chats) {
    chatMessages.innerHTML = "";
    chats.forEach((msg) => addMessage(msg.message, msg.is_user));
  }

  function addMessage(text, isUser = false) {
    const div = document.createElement("div");
    div.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
    const content = document.createElement("div");
    content.className = "message-content";
    content.textContent = text;
    div.appendChild(content);
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function addEventListeners() {
    // Session select
    sessionList.addEventListener("click", async (e) => {
      const li = e.target.closest(".list-group-item");
      if (!li || e.target.classList.contains("group-menu-trigger")) return;
      currentSessionId = li.dataset.sessionId;
      document.querySelectorAll(".document-groups .list-group-item").forEach((i) => i.classList.remove("active"));
      li.classList.add("active");
      await loadSessionData(currentSessionId);
    });

    // Session context menu (rename/delete)
    sessionList.addEventListener("click", (e) => {
      if (e.target.classList.contains("group-menu-trigger")) {
        e.preventDefault();
        e.stopPropagation();
        currentContextTarget = e.target.closest(".list-group-item");
        const rect = e.target.getBoundingClientRect();
        groupContextMenu.style.top = `${rect.bottom}px`;
        groupContextMenu.style.left = `${rect.left}px`;
        groupContextMenu.classList.add("show");
      } 
      // else if (!e.target.closest(".group-context-menu")) {
      //   groupContextMenu.classList.remove("show");
      // }
    });

    document.addEventListener("click", (e) => {
      if (!e.target.closest(".group-context-menu") && !e.target.classList.contains("group-menu-trigger")) {
        groupContextMenu.classList.remove("show");
      }
    });

    document.querySelector(".rename-group").addEventListener("click", async () => {
      const id = currentContextTarget.dataset.sessionId;
      const newName = prompt("New session name:", currentContextTarget.textContent.trim());
      if (!newName) return;
      try {
        const res = await fetch(`http://127.0.0.1:5000/sessions/${id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: newName })
        });
        if (!res.ok) throw new Error("Failed to rename session");
        groupContextMenu.classList.remove("show");
        await loadSessions();
      } catch (error) {
        console.error("Error renaming session:", error);
        alert("Failed to rename session. Please try again.");
      }
    });

    document.querySelector(".delete-group").addEventListener("click", async () => {
      const id = currentContextTarget.dataset.sessionId;
      if (!confirm("Delete this session?")) return;
      try {
        const res = await fetch(`http://127.0.0.1:5000/sessions/${id}`, { method: "DELETE" });
        if (!res.ok) {
          const errorData = await res.json(); // Get error info from backend
          throw new Error(errorData.error || "Error deleting session");
        }
        groupContextMenu.classList.remove("show");
        if (currentSessionId === id) {
          currentSessionId = null;
          fileList.innerHTML = "";
          linkList.innerHTML = "";
          chatMessages.innerHTML = "";
        }
        await loadSessions();
      } catch (error) {
        console.error("Error deleting session:", error);
        alert(`Failed to delete session: ${error.message}`);
      }
    });

    // Add session
    addSessionBtn.addEventListener("click", () => {
      document.getElementById("groupModalTitle").textContent = "Add New Group";
      document.getElementById("groupName").value = "";
      groupModal.show();
      document.getElementById("saveGroupBtn").onclick = async () => {
        const name = document.getElementById("groupName").value.trim();
        if (!name) return;
        try {
          const res = await fetch(`http://127.0.0.1:5000/sessions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
          });
          if (!res.ok) {
            const errorData = await res.json();
            throw new Error(`Failed to add session: ${errorData.error || res.statusText}`);
          }
          groupModal.hide();
          await loadSessions();
        } catch (error) {
          console.error("Error adding session");
          alert(`Failed to add session: ${error.message}`);
        }
      };
    });

    // Upload file
    uploadFileBtn.addEventListener("click", () => {
      if (!currentSessionId) return alert("Select a group first.");
      fileUpload.click();
    });
    fileUpload.addEventListener("change", async () => {
      if (!fileUpload.files.length) return;
      const fd = new FormData();
      fd.append('file', fileUpload.files[0]);
      try {
        const res = await fetch(`http://127.0.0.1:5000/sessions/${currentSessionId}/upload`, { method: 'POST', body: fd });
        if (!res.ok) return alert('Upload failed');
        await loadSessionData(currentSessionId);
      } catch (error) {
        console.error("Error uploading file:", error);
        alert("Failed to upload file. Please try again.");
      }
    });

    // Add link
    addLinkBtn.addEventListener("click", () => {
      if (!currentSessionId) return alert("Select a session first.");
      document.getElementById("linkName").value = "";
      document.getElementById("linkUrl").value = "";
      linkModal.show();
      document.getElementById("saveLinkBtn").onclick = async () => {
        const url = document.getElementById("linkUrl").value.trim();
        if (!url) return;
        try {
          const res = await fetch(`http://127.0.0.1:5000/sessions/${currentSessionId}/links`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
          });
          if (!res.ok) throw new Error("Failed to add link");
          linkModal.hide();
          await loadSessionData(currentSessionId);
        } catch (error) {
          console.error("Error adding link:", error);
          alert("Failed to add link. Please try again.");
        }
      };
    });

    // Send message
    sendBtn.addEventListener("click", sendMessage);
    chatInput.addEventListener("keypress", e => {
      if (e.key === 'Enter' && !e.shiftKey) { 
        e.preventDefault(); 
        sendMessage(); 
      }
    });

    async function sendMessage() {
      const text = chatInput.value.trim();
      if (!text || !currentSessionId) {
        alert("Please select a session and enter a message.");
        return;
      }
      const selectedFileIds = Array.from(document.querySelectorAll('.file-item input:checked')).map(cb => cb.closest('.file-item').dataset.id);
      const selectedLinkIds = Array.from(document.querySelectorAll('.link-item input:checked')).map(cb => cb.closest('.link-item').dataset.id);
      addMessage(text, true);
      chatInput.value = "";
      try {
        const res = await fetch(`http://127.0.0.1:5000/sessions/${currentSessionId}/ask`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: text, file_ids: selectedFileIds, link_ids: selectedLinkIds })
        });
        if (!res.ok) throw new Error("Failed to send message");
        const { answer } = await res.json();
        addMessage(answer, false);
      } catch (error) {
        console.error("Error sending message:", error);
        addMessage("An error occurred while sending the message.", false);
      }
    }
  }

  init();
});
