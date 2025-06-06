document.addEventListener("DOMContentLoaded", function () {
  // DOM Elements
  const documentGroups = document.querySelector(".document-groups");
  const groupContextMenu = document.querySelector(".group-context-menu");
  const itemContextMenu = document.querySelector(".item-context-menu");
  const fileList = document.querySelector(".file-list");
  const linkList = document.querySelector(".link-list");
  const chatMessages = document.getElementById("chatMessages");
  const chatInput = document.getElementById("chatInput");
  const sendBtn = document.getElementById("sendBtn");
  const addGroupBtn = document.querySelector(".add-group-btn");
  const uploadFileBtn = document.querySelector(".upload-file-btn");
  const fileUpload = document.getElementById("fileUpload");
  const addLinkBtn = document.querySelector(".add-link-btn");

  // Bootstrap Modals
  const groupModal = new bootstrap.Modal(document.getElementById("groupModal"));
  const linkModal = new bootstrap.Modal(document.getElementById("linkModal"));
  const renameModal = new bootstrap.Modal(
    document.getElementById("renameModal")
  );

  // State Variables
  let currentGroup = null;
  let currentContextTarget = null;
  let currentItemType = null; // 'file', 'link', or 'group'

  // Data Storage with expiration
  const STORAGE_KEY = "chatbot_data";
  // const EXPIRATION_DAYS = 3;
  const EXPIRATION_DAYS = 1;
  //! Data Storage (In a real app, this would be stored in a database)

  // Restore data from localStorage / initialize default data
  function getStoredData() {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try{
        const { data, timestamp } = JSON.parse(stored);
        const now = new Date();
        const storedDate = new Date(timestamp);
        const diffTime = Math.abs(now - storedDate);
        // const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        const diffDays = Math.ceil(diffTime / (1000 * 60)); //! minute
        if (diffDays <= EXPIRATION_DAYS) {
          return data;
        }
      } catch (e) {
        console.error("localStorage data is invalid:", e);
        localStorage.removeItem(STORAGE_KEY); // Delete corrupted data
      }
    }

    // Default data if expired/doesn't have stored data
    return {
      groups: [
        { id: "compliance", name: "Compliance", files: [], links: [] },
        { id: "hardware-management", name: "Hardware Management", files: [], links: [] },
        { id: "operations", name: "Operations", files: [], links: [] },
        { id: "risk", name: "Risk", files: [], links: [] },
        { id: "software-development", name: "Software Development", files: [], links: [] },
        { id: "vendor-management", name: "Vendor Management", files: [], links: [] },
      ],
      chats: {}, // Save chat history for each group chats
    };
  }

  // Save data in localStorage
  function saveData() {
    const now = new Date();
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        data: {
          groups: data.groups,
          chats: data.chats,
        },
        timestamp: now.toISOString(),
      })
    );
  }

  const data = getStoredData();

  // Initialize the UI
  function init() {
    console.log("Initialize with data:", data);
    // Add event listeners
    addEventListeners();

    // Sort groups alphabetically
    sortGroups();

    // Render the document groups
    renderDocumentGroups();
    //! New
    if (currentGroup) {
      renderChatHistory(currentGroup);
    }
  }

  // Sort groups alphabetically by name
  function sortGroups() {
    data.groups.sort((a, b) => a.name.localeCompare(b.name));
  }

  // Render the document groups in the left sidebar
  function renderDocumentGroups() {
    documentGroups.innerHTML = "";

    data.groups.forEach((group) => {
      const li = document.createElement("li");
      li.className =
        "list-group-item d-flex justify-content-between align-items-center";
      li.dataset.group = group.id;
      li.textContent = group.name;

      const icon = document.createElement("i");
      icon.className = "fas fa-ellipsis-v group-menu-trigger";
      li.appendChild(icon);

      documentGroups.appendChild(li);
    });
  }

  // Render files for the selected group
  function renderFiles() {
    if (!currentGroup) {
      fileList.innerHTML =
        '<p class="text-muted text-center">Select a document group to view files</p>';
      return;
    }

    const group = data.groups.find((g) => g.id === currentGroup);

    if (!group || group.files.length === 0) {
      fileList.innerHTML =
        '<p class="text-muted text-center">No files in this group</p>';
      return;
    }

    fileList.innerHTML = "";

    group.files.forEach((file) => {
      const fileItem = document.createElement("div");
      fileItem.className = "file-item d-flex align-items-center";
      fileItem.dataset.id = file.id;

      // Determine icon based on file type
      let iconClass = "fas fa-file";
      if (file.type === "pdf") iconClass = "fas fa-file-pdf";
      else if (file.type === "docx") iconClass = "fas fa-file-word";
      else if (file.type === "doc") iconClass = "fas fa-file-word";
      else if (file.type === "xlsx") iconClass = "fas fa-file-excel";

      fileItem.innerHTML = `
                <div class="file-icon"><i class="${iconClass}"></i></div>
                <div class="file-name">${file.name}</div>
                <div class="file-checkbox">
                    <input type="checkbox" class="form-check-input">
                </div>
            `;

      fileList.appendChild(fileItem);
    });
  }

  // Render links for the selected group
  function renderLinks() {
    if (!currentGroup) {
      linkList.innerHTML =
        '<p class="text-muted text-center">Select a document group to view links</p>';
      return;
    }

    const group = data.groups.find((g) => g.id === currentGroup);

    if (!group || group.links.length === 0) {
      linkList.innerHTML =
        '<p class="text-muted text-center">No links in this group</p>';
      return;
    }

    linkList.innerHTML = "";

    group.links.forEach((link) => {
      const linkItem = document.createElement("div");
      linkItem.className = "link-item d-flex align-items-center";
      linkItem.dataset.id = link.id;

      linkItem.innerHTML = `
                <div class="link-icon"><i class="fas fa-link"></i></div>
                <div class="link-name">${link.name}</div>
                <div class="link-checkbox">
                    <input type="checkbox" class="form-check-input">
                </div>
            `;

      linkList.appendChild(linkItem);
    });
  }


  //! Render chat history for the selected group
  // function renderChatHistory(groupId) {
  //   chatMessages.innerHTML = "";
  //   const chatHistory = data.chats[groupId] || [];
  //   chatHistory.forEach((message) => {
  //     addMessage(message.text, message.isUser);
  //   });
  // }

  function renderChatHistory(groupId) {
    chatMessages.innerHTML = "";
    if (!data || !data.chats || !data.chats[groupId]) {
      // addMessage("Welcome to this chat!", false); // Default message
      return; // Check if data is not undefined and has chat history for current group
    }

    // chatMessages.innerHTML = "";
    const chatHistory = data.chats[groupId];
    chatHistory.forEach((message) => {
      addMessage(message.text, message.isUser);
    });
  }

  // Add a new message to the chat
  function addMessage(text, isUser = false) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${isUser ? "user-message" : "bot-message"}`;

    const messageContent = document.createElement("div");
    messageContent.className = "message-content";
    messageContent.textContent = text;

    messageDiv.appendChild(messageContent);
    chatMessages.appendChild(messageDiv);

    // Scroll to the bottom of the chat
    chatMessages.scrollTop = chatMessages.scrollHeight;

    //! Save messages into current group's chat history
    if (currentGroup) {
      if (!data.chats[currentGroup]) {
        data.chats[currentGroup] = [];
      }
      data.chats[currentGroup].push({ text, isUser });
      if (data.chats[currentGroup].length > 50) {
        data.chats[currentGroup].shift(); // Delete oldest message
      }
      saveData();
    }
  }

  // Handle sending a message
  async function sendMessage() {
    const text = chatInput.value.trim();
    if (text === "") return;

    //! Get ticked PDFs
    const selectedFiles = Array.from(
      document.querySelectorAll(".file-item input[type='checkbox']:checked")
    ).map((checkbox) => {
      const fileItem = checkbox.closest(".file-item");
      const fileName = fileItem.querySelector(".file-name").textContent;
      const group = data.groups.find((g) => g.id === currentGroup);
      const file = group.files.find((f) => f.name === fileName);
      return file.path;  // Send file path instead of name
    });

    //! Get ticked URLs
    const selectedLinks = Array.from(
      document.querySelectorAll(".link-item input[type='checkbox']:checked")
    ).map((checkbox) => {
      const linkItem = checkbox.closest(".link-item");
      const linkName = linkItem.querySelector(".link-name").textContent;
      const group = data.groups.find((g) => g.id === currentGroup);
      const link = group.links.find((l) => l.name === linkName);
      return link.url;  // Send URL instead of name
    });

    // Check if any PDFs or links are ticked
    if (selectedFiles.length === 0 && selectedLinks.length === 0) {
      alert("Please select at least one file or link to process.");
      return;
    }

    // Add user message to UI
    addMessage(text, true);

    // Clear input
    chatInput.value = "";

    // Send request to Flask backend
    try {
      // addMessage("Đang xử lý...", false);
      const response = await fetch("http://127.0.0.1:5000/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          question: text,
          files: selectedFiles,
          links: selectedLinks,
        }),
      });
        
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }

      const responseData = await response.json();

      // Display answer from chatbot
      addMessage(responseData.answer, false);

      // Display source if there is
      if (responseData.sources && responseData.sources.length > 0) {
        addMessage(`Source: ${responseData.sources.join(", ")}`, false);
      }
    } catch (error) {
      console.error("Error:", error);
      addMessage("An error occurred while submitting question", false);
    }
  }

  // Generate a unique ID
  function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  // Add a new group
  function addGroup(name) {
    const id = name.toLowerCase().replace(/\s+/g, "-");
    data.groups.push({ id, name, files: [], links: [] });
    sortGroups();
    renderDocumentGroups();
    //! New
    saveData();
  }

  // Rename a group
  function renameGroup(id, newName) {
    const group = data.groups.find((g) => g.id === id);
    if (group) {
      group.name = newName;
      sortGroups();
      renderDocumentGroups();
      //! New
      saveData();
    }
  }

  // Delete a group
  function deleteGroup(id) {
    const index = data.groups.findIndex((g) => g.id === id);
    if (index !== -1) {
      data.groups.splice(index, 1);
      //! New
      delete data.chats[id]; // Delete group chat's history
      renderDocumentGroups();
      //! New
      saveData();

      if (currentGroup === id) {
        currentGroup = null;
        renderFiles();
        renderLinks();
        //! New
        chatMessages.innerHTML = "";
      }
    }
  }

  // Add a file to the current group
  function addFile(name, type, path) {
    if (!currentGroup) return;

    const group = data.groups.find((g) => g.id === currentGroup);
    if (group) {
      group.files.push({
        id: generateId(),
        name,
        type,
        path, //! Save file path
      });
      renderFiles();
      //! New
      saveData();
    }
  }

  // Add a link to the current group
  function addLink(name, url) {
    if (!currentGroup) return;

    const group = data.groups.find((g) => g.id === currentGroup);
    if (group) {
      group.links.push({
        id: generateId(),
        name,
        url, //! Save URL
      });
      renderLinks();
      //! New
      saveData();
    }
  }

  // Rename an item (file or link)
  function renameItem(id, newName, type) {
    if (!currentGroup) return;

    const group = data.groups.find((g) => g.id === currentGroup);
    if (!group) return;

    if (type === "file") {
      const file = group.files.find((f) => f.id === id);
      if (file) {
        file.name = newName;
        renderFiles();
        //! New
        saveData();
      }
    } else if (type === "link") {
      const link = group.links.find((l) => l.id === id);
      if (link) {
        link.name = newName;
        renderLinks();
        //! New
        saveData();
      }
    }
  }

  // Delete an item (file or link)
  function deleteItem(id, type) {
    if (!currentGroup) return;

    const group = data.groups.find((g) => g.id === currentGroup);
    if (!group) return;

    if (type === "file") {
      const index = group.files.findIndex((f) => f.id === id);
      if (index !== -1) {
        group.files.splice(index, 1);
        renderFiles();
        //! New
        saveData();
      }
    } else if (type === "link") {
      const index = group.links.findIndex((l) => l.id === id);
      if (index !== -1) {
        group.links.splice(index, 1);
        renderLinks();
        //! New
        saveData();
      }
    }
  }

  // Event Listeners
  function addEventListeners() {
    // Document Group Selection
    documentGroups.addEventListener("click", function (e) {
      const li = e.target.closest(".list-group-item");
      if (li && !e.target.classList.contains("group-menu-trigger")) {
        console.log("Change to group:", li.dataset.group);
        // Remove active class from all items
        document
          .querySelectorAll(".document-groups .list-group-item")
          .forEach((item) => {
            item.classList.remove("active");
          });

        // Add active class to selected item
        li.classList.add("active");

        // Update current group
        currentGroup = li.dataset.group;

        // Render files and links for the selected group
        renderFiles();
        renderLinks();
        //! New
        renderChatHistory(currentGroup); // Show chat history of new group
      }
    });

    // Group Context Menu
    document.addEventListener("click", function (e) {
      if (e.target.classList.contains("group-menu-trigger")) {
        e.preventDefault();
        e.stopPropagation();

        // Set current context target
        currentContextTarget = e.target.closest(".list-group-item");
        currentItemType = "group";

        // Position and show context menu
        const rect = e.target.getBoundingClientRect();
        groupContextMenu.style.top = `${rect.bottom}px`;
        groupContextMenu.style.left = `${rect.left}px`;
        groupContextMenu.classList.add("show");
      } else if (!e.target.closest(".group-context-menu")) {
        // Hide context menu if clicking elsewhere
        groupContextMenu.classList.remove("show");
      }
    });

    // File/Link Context Menu
    document.addEventListener("contextmenu", function (e) {
      const fileItem = e.target.closest(".file-item");
      const linkItem = e.target.closest(".link-item");

      if (fileItem || linkItem) {
        e.preventDefault();

        // Set current context target
        currentContextTarget = fileItem || linkItem;
        currentItemType = fileItem ? "file" : "link";

        // Position and show context menu
        itemContextMenu.style.top = `${e.clientY}px`;
        itemContextMenu.style.left = `${e.clientX}px`;
        itemContextMenu.classList.add("show");
      } else {
        itemContextMenu.classList.remove("show");
      }
    });

    // Hide context menus when clicking elsewhere
    document.addEventListener("click", function (e) {
      if (
        !e.target.closest(".item-context-menu") &&
        !e.target.closest(".file-item") &&
        !e.target.closest(".link-item")
      ) {
        itemContextMenu.classList.remove("show");
      }
    });

    // Rename Group
    document
      .querySelector(".rename-group")
      .addEventListener("click", function () {
        if (currentContextTarget && currentItemType === "group") {
          const groupId = currentContextTarget.dataset.group;
          const group = data.groups.find((g) => g.id === groupId);

          if (group) {
            // Set modal title and input value
            document.getElementById("groupModalTitle").textContent =
              "Rename Group";
            document.getElementById("groupName").value = group.name;

            // Show modal
            groupModal.show();

            // Set up save button
            document.getElementById("saveGroupBtn").onclick = function () {
              const newName = document.getElementById("groupName").value.trim();
              if (newName) {
                renameGroup(groupId, newName);
                groupModal.hide();
              }
            };
          }

          // Hide context menu
          groupContextMenu.classList.remove("show");
        }
      });

    // Delete Group
    document
      .querySelector(".delete-group")
      .addEventListener("click", function () {
        if (currentContextTarget && currentItemType === "group") {
          const groupId = currentContextTarget.dataset.group;

          if (confirm("Are you sure you want to delete this group?")) {
            deleteGroup(groupId);
          }

          // Hide context menu
          groupContextMenu.classList.remove("show");
        }
      });

    // Rename Item (File or Link)
    document
      .querySelector(".rename-item")
      .addEventListener("click", function () {
        if (
          currentContextTarget &&
          (currentItemType === "file" || currentItemType === "link")
        ) {
          const itemId = currentContextTarget.dataset.id;
          const itemName = currentContextTarget.querySelector(
            `.${currentItemType}-name`
          ).textContent;

          // Set modal input value
          document.getElementById("newItemName").value = itemName;

          // Show modal
          renameModal.show();

          // Set up save button
          document.getElementById("saveRenameBtn").onclick = function () {
            const newName = document.getElementById("newItemName").value.trim();
            if (newName) {
              renameItem(itemId, newName, currentItemType);
              renameModal.hide();
            }
          };

          // Hide context menu
          itemContextMenu.classList.remove("show");
        }
      });

    // Delete Item (File or Link)
    document
      .querySelector(".delete-item")
      .addEventListener("click", function () {
        if (
          currentContextTarget &&
          (currentItemType === "file" || currentItemType === "link")
        ) {
          const itemId = currentContextTarget.dataset.id;

          if (
            confirm(`Are you sure you want to delete this ${currentItemType}?`)
          ) {
            deleteItem(itemId, currentItemType);
          }

          // Hide context menu
          itemContextMenu.classList.remove("show");
        }
      });

    // Add Group Button
    addGroupBtn.addEventListener("click", function () {
      // Reset modal title and input value
      document.getElementById("groupModalTitle").textContent = "Add New Group";
      document.getElementById("groupName").value = "";

      // Show modal
      groupModal.show();

      // Set up save button
      document.getElementById("saveGroupBtn").onclick = function () {
        const name = document.getElementById("groupName").value.trim();
        if (name) {
          addGroup(name);
          groupModal.hide();
        }
      };
    });

    // Upload File Button
    uploadFileBtn.addEventListener("click", function () {
      if (!currentGroup) {
        alert("Please select a document group first.");
        return;
      }

      fileUpload.click();
    });

    // File Upload Change
    fileUpload.addEventListener("change", async function () {
      if (this.files.length > 0) {
        const file = this.files[0];
        const fileName = file.name;

        // Check file extension
        const extension = fileName.split(".").pop().toLowerCase();
        if (["pdf", "docx", "xlsx", "doc"].indexOf(extension) === -1) {
          alert("Only PDF, DOCX, DOC, and XLSX files are allowed.");
          return;
        }

        // Upload files to server
        const formData = new FormData();
        formData.append("file", file); // Add file to FormData

        try {
          const response = await fetch("http://127.0.0.1:5000/upload", {
            method: "POST",
            body: formData,
          });
          
          if (!response.ok) {
            throw new Error("Upload failed");
          }

          const responseData = await response.json();
          const filepath = responseData.path; // Get path from server

          // Call addFile with path from server
          addFile(fileName, extension, filepath);

          // Reset file input
          this.value = "";
        } catch (error) {
          console.error("Error uploading file:", error);
          alert("An error occurred while uploading file, please try again!");
        }
      }
    });

    // Add Link Button
    addLinkBtn.addEventListener("click", function () {
      if (!currentGroup) {
        alert("Please select a document group first.");
        return;
      }

      // Reset modal input values
      document.getElementById("linkName").value = "";
      document.getElementById("linkUrl").value = "";

      // Show modal
      linkModal.show();
    });

    // Save Link Button
    document
      .getElementById("saveLinkBtn")
      .addEventListener("click", function () {
        const name = document.getElementById("linkName").value.trim();
        const url = document.getElementById("linkUrl").value.trim();

        if (name && url) {
          addLink(name, url);
          linkModal.hide();
        }
      });

    // Send Button
    sendBtn.addEventListener("click", sendMessage);

    // Enter key in chat input
    chatInput.addEventListener("keypress", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
  }

  // Initialize the app
  init();
});
