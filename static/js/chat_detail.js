function initChatDetail() {
  const dataEl = document.getElementById("chat-detail");
  if (!dataEl) return;

  const { username, roomid, targetuser } = dataEl.dataset;

  let localStream, peerConnection;
  const config = { iceServers: [{ urls: "stun:stun.l.google.com:19302" }] };

  const localVideo = document.getElementById("localVideo");
  const remoteVideo = document.getElementById("remoteVideo");
  const callScreen = document.getElementById("call-screen");
  const endCallBtn = document.getElementById("end-call");
  const audioCallBtn = document.getElementById("audio-call-btn");
  const videoCallBtn = document.getElementById("video-call-btn");
  const messageInput = document.getElementById("message-input");
  const sendButton = document.getElementById("send-button");
  const chatArea = document.getElementById("chat_area");
  const attachmentInput = document.getElementById("attachment-input");

  let selectedFile = null,
    selectedFileBase64 = null;

  const wsScheme = window.location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(
    `${wsScheme}://${window.location.host}/ws/chat/${roomid}/`
  );

  /* -------------------- Messaging -------------------- */
  if (sendButton && messageInput) {
    sendButton.addEventListener("click", () => {
      const message = messageInput.value.trim();
      if (message !== "") {
        socket.send(JSON.stringify({ type: "message", message, username }));
        messageInput.value = "";
      }
    });

    messageInput.addEventListener("input", () => {
      socket.send(JSON.stringify({ type: "typing", user: username }));
    });

    messageInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        sendButton.click();
      }
    });
  }

  function appendMessage(sender, message) {
    const isMine = sender === username;
    const msgDiv = document.createElement("div");
    const time = new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

    msgDiv.className = `flex ${isMine ? "justify-end" : "justify-start"}`;
    msgDiv.innerHTML = `
      <div class="${
        isMine ? "bg-[#00a63e] text-white" : "bg-white border border-gray-200"
      } px-4 py-2 rounded-xl text-sm max-w-xs">
        ${message}
        <sub class="text-[10px] opacity-60">${time}</sub>
      </div>
    `;
    if (chatArea) {
      chatArea.appendChild(msgDiv);
      chatArea.scrollTop = chatArea.scrollHeight;
    }
  }

  /* -------------------- Call Handling -------------------- */
  if (audioCallBtn) audioCallBtn.onclick = () => startCall("audio");
  if (videoCallBtn) videoCallBtn.onclick = () => startCall("video");
  if (endCallBtn) endCallBtn.onclick = endCall;

  function startCall(callType) {
    navigator.mediaDevices
      .getUserMedia({ video: callType === "video", audio: true })
      .then((stream) => {
        localStream = stream;
        if (localVideo) localVideo.srcObject = stream;
        if (callScreen) callScreen.classList.remove("hidden");

        createPeerConnection();
        localStream
          .getTracks()
          .forEach((track) => peerConnection.addTrack(track, localStream));

        peerConnection.createOffer().then((offer) => {
          peerConnection.setLocalDescription(offer);
          socket.send(
            JSON.stringify({
              type: "webrtc_offer",
              offer,
              from: username,
              callType,
            })
          );
        });

        socket.send(
          JSON.stringify({
            type: "call",
            call_type: callType,
            target_user: targetuser,
          })
        );
      })
      .catch(console.error);
  }

  function createPeerConnection() {
    peerConnection = new RTCPeerConnection(config);

    peerConnection.onicecandidate = (event) => {
      if (event.candidate) {
        socket.send(
          JSON.stringify({
            type: "ice_candidate",
            candidate: event.candidate,
            from: username,
          })
        );
      }
    };

    peerConnection.ontrack = (event) => {
      if (remoteVideo) remoteVideo.srcObject = event.streams[0];
    };
  }

  /* ----------- End Call for Both Users ----------- */
  function endCall() {
    // Close local connection
    if (peerConnection) {
      peerConnection.close();
      peerConnection = null;
    }
    if (localStream) {
      localStream.getTracks().forEach((track) => track.stop());
    }
    if (callScreen) callScreen.classList.add("hidden");

    // Notify other user
    socket.send(
      JSON.stringify({
        type: "call_end",
        from: username,
      })
    );
  }

  function handleMediaMessage(data) {
    const isMine = data.user === username;
    const time = new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

    const msgDiv = document.createElement("div");
    msgDiv.className = `flex ${isMine ? "justify-end" : "justify-start"} my-1`;

    const bubbleDiv = document.createElement("div");
    bubbleDiv.className = `${
      isMine ? "bg-[#00a63e] text-white" : "bg-white border border-gray-200"
    } px-4 py-2 rounded-xl text-sm max-w-xs break-words`;

    const byteCharacters = atob(data.file.data);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: data.file.type });
    const fileUrl = URL.createObjectURL(blob);

    if (data.file.type.startsWith("image/")) {
      const img = document.createElement("img");
      img.src = fileUrl;
      img.style.maxWidth = "200px";
      img.style.borderRadius = "8px";
      bubbleDiv.appendChild(img);
    } else if (data.file.type.startsWith("video/")) {
      const video = document.createElement("video");
      video.src = fileUrl;
      video.controls = true;
      video.style.maxWidth = "300px";
      video.style.borderRadius = "8px";
      bubbleDiv.appendChild(video);
    } else {
      const link = document.createElement("a");
      link.href = fileUrl;
      link.download = data.file.name;
      link.textContent = `📄 ${data.file.name}`;
      link.target = "_blank";
      link.style.color = isMine ? "white" : "blue";
      bubbleDiv.appendChild(link);
    }

    const timeEl = document.createElement("sub");
    timeEl.className = "text-[10px] opacity-60 ml-2";
    timeEl.textContent = time;
    bubbleDiv.appendChild(timeEl);

    msgDiv.appendChild(bubbleDiv);

    if (chatArea) {
      chatArea.appendChild(msgDiv);
      chatArea.scrollTop = chatArea.scrollHeight;
    }
  }

  // -----------------Socket message handling------------------
  socket.onmessage = async function (e) {
    const data = JSON.parse(e.data);

    switch (data.type) {
      case "message":
        appendMessage(data.user, data.message);
        break;
      case "typing":
        console.log(`${data.user} is typing...`);
        break;
      case "media":
        handleMediaMessage(data);
        break;
      case "webrtc_offer":
        if (data.from !== username)
          await handleOffer(data.offer, data.callType);
        break;
      case "webrtc_answer":
        if (data.from !== username)
          await peerConnection.setRemoteDescription(
            new RTCSessionDescription(data.answer)
          );
        break;
      case "ice_candidate":
        if (data.from !== username)
          await peerConnection.addIceCandidate(
            new RTCIceCandidate(data.candidate)
          );
        break;
      case "call_end":
        if (data.from !== username) {
          // Remote user ended call → close it locally too
          if (peerConnection) peerConnection.close();
          if (localStream)
            localStream.getTracks().forEach((track) => track.stop());
          if (callScreen) callScreen.classList.add("hidden");
          peerConnection = null;
        }
        break;
      // --- Incoming Call Notification ---
      case "notification":
        if (data.event === "call") {
          console.log(`Incoming ${data.call_type} call from ${data.from_user}`);

          // Show popup UI (basic example)
          if (
            confirm(
              `${data.from_user} is calling you (${data.call_type}). Accept?`
            )
          ) {
            // Will accept when offer arrives
          } else {
            // Send reject signal
            socket.send(
              JSON.stringify({
                type: "call_end",
                from: username,
                to: data.from_user,
              })
            );
          }
        }
        break;
      // --- Unknown events ---
      default:
        console.warn("Unhandled event:", data);
    }
  };

  async function handleOffer(offer, callType = "video") {
    createPeerConnection();

    navigator.mediaDevices
      .getUserMedia({ video: callType === "video", audio: true })
      .then(async (stream) => {
        localStream = stream;
        if (localVideo) localVideo.srcObject = stream;
        if (callScreen) callScreen.classList.remove("hidden");

        stream
          .getTracks()
          .forEach((track) => peerConnection.addTrack(track, stream));
        await peerConnection.setRemoteDescription(
          new RTCSessionDescription(offer)
        );

        const answer = await peerConnection.createAnswer();
        await peerConnection.setLocalDescription(answer);

        socket.send(
          JSON.stringify({ type: "webrtc_answer", answer, from: username })
        );
      });
  }

  /* ---------------- File Attachment Handling ---------------- */
  if (attachmentInput) {
    attachmentInput.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = function () {
        selectedFile = file;
        selectedFileBase64 = reader.result.split(",")[1];

        const fileThumb = document.getElementById("file-thumb");
        if (fileThumb) {
          if (file.type.startsWith("image/")) {
            fileThumb.innerHTML = `<img src="${reader.result}" class="w-full h-full object-cover" alt="preview" />`;
          } else {
            fileThumb.innerHTML = `<div class="w-full h-full flex items-center justify-center text-gray-400 text-xl">📄</div>`;
          }
        }

        if (document.getElementById("file-name"))
          document.getElementById("file-name").textContent =
            file.name.split(".")[0];
        if (document.getElementById("file-type"))
          document.getElementById("file-type").textContent =
            file.type || "Unknown type";
        if (document.getElementById("file-preview"))
          document.getElementById("file-preview").classList.remove("hidden");
      };

      reader.readAsDataURL(file);
    });
  }

  const removeFileBtn = document.getElementById("remove-file");
  if (removeFileBtn) {
    removeFileBtn.addEventListener("click", () => {
      const thumb = document.getElementById("file-thumb");
      if (thumb) thumb.innerHTML = "";
      if (document.getElementById("file-name"))
        document.getElementById("file-name").textContent = "";
      if (document.getElementById("file-type"))
        document.getElementById("file-type").textContent = "";
      selectedFile = null;
      selectedFileBase64 = null;
      if (attachmentInput) attachmentInput.value = "";
      if (document.getElementById("file-preview"))
        document.getElementById("file-preview").classList.add("hidden");
    });
  }

  const sendMediaFileBtn = document.getElementById("sendMediafile");
  if (sendMediaFileBtn) {
    sendMediaFileBtn.addEventListener("click", () => {
      if (!selectedFile || !selectedFileBase64) {
        alert("No file selected.");
        return;
      }

      const tempId = `temp-${Date.now()}`;
      const sendingDiv = document.createElement("div");
      sendingDiv.className = "flex justify-end my-1";
      sendingDiv.innerHTML = `
        <div id="${tempId}" class="bg-[#00a63e] text-white px-4 py-2 rounded-xl text-sm max-w-xs flex items-center gap-2">
          📤 Sending ${selectedFile.name}...
          <span class="animate-pulse">⏳</span>
        </div>
      `;
      chatArea.scrollTop = chatArea.scrollHeight;

      socket.send(
        JSON.stringify({
          type: "media",
          file: {
            name: selectedFile.name,
            type: selectedFile.type,
            data: selectedFileBase64,
          },
          user: username,
        })
      );

      if (document.getElementById("file-thumb"))
        document.getElementById("file-thumb").innerHTML = "";
      if (document.getElementById("file-name"))
        document.getElementById("file-name").textContent = "";
      if (document.getElementById("file-type"))
        document.getElementById("file-type").textContent = "";
      selectedFile = null;
      selectedFileBase64 = null;
      if (attachmentInput) attachmentInput.value = "";
      if (document.getElementById("file-preview"))
        document.getElementById("file-preview").classList.add("hidden");
    });
  }
}

document.addEventListener("DOMContentLoaded", initChatDetail);
document.body.addEventListener("htmx:afterSwap", initChatDetail);
