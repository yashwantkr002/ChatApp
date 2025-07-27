// const roomId = "{{ room.id }}";  // Use your Django context here
const roomId = "Abc";  // Use your Django context here
const username = "{{ request.user.username }}";
const socket = new WebSocket(`ws://${window.location.host}/ws/chat/${roomId}/`);

let localStream;
let peerConnection;
const config = {
  iceServers: [{ urls: "stun:stun.l.google.com:19302" }]
};


const localVideo = document.getElementById("localVideo");
const remoteVideo = document.getElementById("remoteVideo");
const callScreen = document.getElementById("call-screen");
const endCallBtn = document.getElementById("end-call");
const audioCallBtn = document.getElementById("audio-call-btn");
const videoCallBtn = document.getElementById("video-call-btn");
const messageInput = document.getElementById("message-input");
const sendButton = document.getElementById("send-button");
const chatArea = document.getElementById("chat-area");

// ========== Message Handlers ==============

// Send message
sendButton.addEventListener("click", () => {
  const message = messageInput.value.trim();
  console.log(message)
  if (message !== "") {
    socket.send(JSON.stringify({
      type: "message",
      message: message,
      username: username
    }));
    appendMessage(username, message); // Instant display
    messageInput.value = "";
  }
});

// Send typing event
messageInput.addEventListener("input", () => {
  socket.send(JSON.stringify({
    type: "typing",
    user: username
  }));
});

// Optional: Send on Enter
messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    sendButton.click();
  }
});

// Display message in chat
function appendMessage(sender, message) {
  const isMine = sender === username;
  const msgDiv = document.createElement("div");
  const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  msgDiv.className = `flex ${isMine ? "justify-end" : "justify-start"}`;
  msgDiv.innerHTML = `
    <div class="${isMine ? "bg-[#00a63e] text-white" : "bg-white border border-gray-200"} px-4 py-2 rounded-xl text-sm max-w-xs">
      ${message}
      <div class="text-[10px] text-right mt-1 opacity-60">${time}</div>
    </div>
  `;
  chatArea.appendChild(msgDiv);
  chatArea.scrollTop = chatArea.scrollHeight;
}

// ========== WebRTC Call Handlers ==========

audioCallBtn.onclick = () => startCall("audio");
videoCallBtn.onclick = () => startCall("video");
endCallBtn.onclick = endCall;

function startCall(callType) {
  navigator.mediaDevices.getUserMedia({
    video: callType === "video",
    audio: true
  }).then(stream => {
    localStream = stream;
    localVideo.srcObject = stream;
    callScreen.classList.remove("hidden");

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
    remoteVideo.srcObject = event.streams[0];
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
  callScreen.classList.add("hidden");
}

// ========== WebSocket Message Handling ==========

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
      localVideo.srcObject = stream;
      callScreen.classList.remove("hidden");

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
