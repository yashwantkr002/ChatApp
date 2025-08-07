
function initChatDetail() {
  const dataEl = document.getElementById("chat-detail");
  if (!dataEl) return;
  const data = dataEl.dataset;
  const username = data.username;
  const roomId = data.roomid;
  
  let localStream;
  let peerConnection;
  const config = {
    iceServers: [{ urls: "stun:stun.l.google.com:19302" }]
  };

  // ========== DOM Elements ==============
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

  let selectedFile = null;
  let selectedFileBase64 = null;

  // ========== Message Handlers ==============
  if (sendButton && messageInput) {
    sendButton.addEventListener("click", () => {
      const message = messageInput.value.trim();
      if (message !== "") {
        socket.send(JSON.stringify({
          type: "message",
          message: message,
          username: username
        }));
        // appendMessage(username, message); // Instant display
        messageInput.value = "";
      }
    });

    messageInput.addEventListener("input", () => {
      socket.send(JSON.stringify({
        type: "typing",
        user: username
      }));
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
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    msgDiv.className = `flex ${isMine ? "justify-end" : "justify-start"}`;
    msgDiv.innerHTML = `
      <div class="${isMine ? "bg-[#00a63e] text-white" : "bg-white border border-gray-200"} px-4 py-2  rounded-xl text-sm max-w-xs">
        ${message}
        <sub class="text-[10px] text-right mt-1  opacity-60">${time}</sub>
      </div>
    `;
    chatArea.appendChild(msgDiv);
    chatArea.scrollTop = chatArea.scrollHeight;
  }

  // ========== WebRTC Call Handlers ===========
  if (audioCallBtn) audioCallBtn.onclick = () => startCall("audio");
  if (videoCallBtn) videoCallBtn.onclick = () => startCall("video");
  if (endCallBtn) endCallBtn.onclick = endCall;

  function startCall(callType) {
    navigator.mediaDevices.getUserMedia({
      video: callType === "video",
      audio: true
    }).then(stream => {
      localStream = stream;
      if (localVideo) localVideo.srcObject = stream;
      if (callScreen) callScreen.classList.remove("hidden");

      createPeerConnection();
      localStream.getTracks().forEach(track => peerConnection.addTrack(track, localStream));

      peerConnection.createOffer().then(offer => {
        peerConnection.setLocalDescription(offer);
        socket.send(JSON.stringify({
          type: "webrtc_offer",
          offer: offer,
          from: username
        }));
      });

      socket.send(JSON.stringify({
        type: "call",
        call_type: callType,
        target_user: "{{ other_user.username }}"
      }));
    }).catch(console.error);
  }

  function createPeerConnection() {
    peerConnection = new RTCPeerConnection(config);

    peerConnection.onicecandidate = (event) => {
      if (event.candidate) {
        socket.send(JSON.stringify({
          type: "ice_candidate",
          candidate: event.candidate,
          from: username
        }));
      }
    };

    peerConnection.ontrack = (event) => {
      if (remoteVideo) remoteVideo.srcObject = event.streams[0];
    };
  }

  function endCall() {
    if (peerConnection) {
      peerConnection.close();
      peerConnection = null;
    }
    if (localStream) {
      localStream.getTracks().forEach(track => track.stop());
    }
    if (callScreen) callScreen.classList.add("hidden");
  }

  // ========== WebSocket Message Handling ===========
  const socket = new WebSocket(`ws://${window.location.host}/ws/chat/${roomId}/`);
  socket.onmessage = async function (e) {
    const data = JSON.parse(e.data);

    switch (data.type) {
      case "message":
        appendMessage(data.user, data.message);
        break;

      case "typing":
        console.log(`${data.user} is typing...`); // You can show a typing indicator here
        break;

      case "webrtc_offer":
        if (data.from !== username) await handleOffer(data.offer);
        break;

      case "webrtc_answer":
        if (data.from !== username) {
          await peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));
        }
        break;

      case "ice_candidate":
        if (data.from !== username) {
          await peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
        }
        break;

      case "read":
        console.log("Message read:", data.message_id);
        break;

      case "notification":
        console.log("Notification:", data.event);
        break;

      default:
        console.warn("Unhandled event:", data);
    }
  };

  async function handleOffer(offer) {
    createPeerConnection();

    navigator.mediaDevices.getUserMedia({ video: true, audio: true })
      .then(async (stream) => {
        localStream = stream;
        if (localVideo) localVideo.srcObject = stream;
        if (callScreen) callScreen.classList.remove("hidden");

        stream.getTracks().forEach(track => peerConnection.addTrack(track, stream));
        await peerConnection.setRemoteDescription(new RTCSessionDescription(offer));

        const answer = await peerConnection.createAnswer();
        await peerConnection.setLocalDescription(answer);

        socket.send(JSON.stringify({
          type: "webrtc_answer",
          answer: answer,
          from: username
        }));
      });
  }

  // ================ Document Display on Frontend ===============
  if (attachmentInput) {
    attachmentInput.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (!file) return;

      const reader = new FileReader();

      reader.onload = function () {
        selectedFile = file;
        selectedFileBase64 = reader.result.split(',')[1];

        const isImage = file.type.startsWith("image/");
        const fileThumb = document.getElementById("file-thumb");

        if (isImage) {
          fileThumb.innerHTML = `<img src="${reader.result}" class="w-full h-full object-cover" alt="preview" />`;
        } else {
          fileThumb.innerHTML = `<div class="w-full h-full flex items-center justify-center text-gray-400 text-xl">📄</div>`;
        }

        document.getElementById("file-name").textContent = file.name;
        document.getElementById("file-type").textContent = file.type || "Unknown type";
        document.getElementById("file-preview").classList.remove("hidden");
      };

      reader.readAsDataURL(file);
    });
  }

  const removeFileBtn = document.getElementById("remove-file");
  if (removeFileBtn) {
    removeFileBtn.addEventListener("click", () => {
      document.getElementById("file-thumb").innerHTML = "";
      document.getElementById("file-name").textContent = "";
      document.getElementById("file-type").textContent = "";
      selectedFile = null;
      selectedFileBase64 = null;
      if (attachmentInput) attachmentInput.value = "";  // Reset file input
      document.getElementById("file-preview").classList.add("hidden");
    });
  }
}

// Remove any top-level variable declarations to avoid redeclaration errors

// Run on page load
document.addEventListener('DOMContentLoaded', initChatDetail);
// Run after HTMX swaps in new chat detail
document.body.addEventListener('htmx:afterSwap', initChatDetail);


