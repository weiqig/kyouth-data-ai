// const backendUrl = window.APP_CONFIG.backendUrl;
const fileInput = document.getElementById('fileInput');
const uploadLabel = document.getElementById('uploadLabel');
const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');

let selectedFile = null;

fileInput.addEventListener('change', (e) => {
	if (e.target.files.length > 0) {
		selectedFile = e.target.files[0];
		uploadLabel.classList.add('file-selected');
		userInput.placeholder = `Selected: ${selectedFile.name}`;
	}
});

async function extractTextFromPDF(file) {
	const arrayBuffer = await file.arrayBuffer();
	const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
	let fullText = "";

	for (let i = 1; i <= pdf.numPages; i++) {
		const page = await pdf.getPage(i);
		const textContent = await page.getTextContent();
		const pageText = textContent.items.map(item => item.str).join(" ");
		fullText += pageText + "\n";
	}
	return fullText;
}

// Function to append a message to the chat
function appendMessage(text, sender) {
	const messageDiv = document.createElement('div');
	messageDiv.classList.add('message', sender);

	if (sender === 'bot') {
		// Convert Markdown to HTML for the bot's response
		messageDiv.innerHTML = marked.parse(text);
	} else {
		// Keep user messages as plain text for security
		messageDiv.textContent = text;
	}

	chatMessages.appendChild(messageDiv);
	chatMessages.scrollTop = chatMessages.scrollHeight;
}

function convertToBase64(file) {
	return new Promise((resolve, reject) => {
		const reader = new FileReader();
		reader.readAsDataURL(file);
		reader.onload = () => resolve(reader.result);
		reader.onerror = error => reject(error);
	});
}

// Handle sending message
async function handleSendMessage() {
	const messageText = userInput.value.trim();
	if (messageText === '' && !selectedFile) return;

	sendBtn.disabled = true;
	userInput.disabled = true;

	let displayPrompt = messageText;
	if (selectedFile && displayPrompt === '') {
		displayPrompt = `[Uploaded File: ${selectedFile.name}]`;
	} else if (selectedFile) {
		displayPrompt += ` \n[File: ${selectedFile.name}]`;
	}

	appendMessage(displayPrompt, 'user');
	userInput.value = '';
	userInput.placeholder = "Type a message...";
	uploadLabel.classList.remove('file-selected');

	const typingDiv = document.createElement('div');
	typingDiv.classList.add('message', 'bot');
	typingDiv.textContent = "...";
	chatMessages.appendChild(typingDiv);
	chatMessages.scrollTop = chatMessages.scrollHeight;

	try {
		let payload = {
			message: messageText,
			pdfText: ""
		};

		// If a file is selected, process it and clear out the state for the next message
		if (selectedFile){
			if (selectedFile.type === "application/pdf") {
				payload.pdfText = await extractTextFromPDF(selectedFile); // Use your function!
				payload.fileType = "pdf";
			}
			else if (selectedFile.type.startsWith("image/")) {
				const base64Image = await convertToBase64(selectedFile);
				// We strip the prefix "data:image/png;base64," if your backend expects raw base64
				// or keep it if your backend handles data URLs. Usually, keeping it is safer.
				payload.imageData = base64Image;
				payload.fileType = "image";
			}
				payload.fileName = selectedFile.name; 
				selectedFile = null;
				fileInput.value = ''; 
		}
		// 3. Make the API call to your Node.js backend
		const response = await fetch("/chat", {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(payload)
		});

		const data = await response.json();
		chatMessages.removeChild(typingDiv);

		if (response.ok) {
			appendMessage(data.reply, 'bot');
		} else {
			appendMessage("Sorry, I encountered an error. Please try again.", 'bot');
		}

	} catch (error) {
		console.error(error);
		chatMessages.removeChild(typingDiv);
		appendMessage("Could not connect to the server.", 'bot');
	} finally {
		sendBtn.disabled = false;
		userInput.disabled = false;
		selectedFile = null;
		fileInput.value = '';
		userInput.focus();
	}
}

// Event Listeners
sendBtn.addEventListener('click', handleSendMessage);

userInput.addEventListener('keypress', (e) => {
	if (e.key === 'Enter') {
		handleSendMessage();
	}
});