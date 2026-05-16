from flask import Flask, request, render_template_string, jsonify, send_file, Response
import socket
import os
import uuid
from datetime import datetime
import base64
import mimetypes

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = None  # No size limit

# Directories for storing files
UPLOAD_DIR = "shared_files"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Store messages
messages = []
last_id = 0

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Two-Way File Sharing</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=yes">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        * {
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e0e0e0;
        }
        .header h3 {
            margin: 0;
            color: #333;
            font-size: 24px;
        }
        .header p {
            margin: 5px 0 0;
            color: #666;
            font-size: 14px;
        }
        .messages {
            height: 450px;
            overflow-y: auto;
            border: 1px solid #e0e0e0;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 8px;
            background: #fafafa;
        }
        .message {
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 10px;
            max-width: 85%;
            position: relative;
            animation: fadeIn 0.3s ease-in;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .message-sent {
            background: #007bff;
            color: white;
            margin-left: auto;
            text-align: right;
        }
        .message-received {
            background: #e9ecef;
            color: black;
            margin-right: auto;
        }
        .message-system {
            background: #fff3cd;
            color: #856404;
            text-align: center;
            margin: 10px auto;
            font-size: 12px;
            max-width: 90%;
        }
        .message-time {
            font-size: 10px;
            opacity: 0.7;
            margin-top: 5px;
        }
        .device-name {
            font-weight: bold;
            margin-bottom: 5px;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .copy-btn {
            background: rgba(0,0,0,0.1);
            border: none;
            border-radius: 5px;
            padding: 4px 10px;
            cursor: pointer;
            font-size: 11px;
            transition: all 0.2s;
            margin-top: 8px;
        }
        .message-received .copy-btn {
            background: rgba(0,0,0,0.1);
            color: #333;
        }
        .message-received .copy-btn:hover {
            background: rgba(0,0,0,0.2);
        }
        .message-sent .copy-btn {
            background: rgba(255,255,255,0.2);
            color: white;
        }
        .message-sent .copy-btn:hover {
            background: rgba(255,255,255,0.3);
        }
        .file-info {
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }
        .file-icon {
            font-size: 32px;
        }
        .file-details {
            flex: 1;
        }
        .file-name {
            font-weight: bold;
            word-break: break-all;
            font-size: 14px;
        }
        .file-size {
            font-size: 11px;
            opacity: 0.7;
        }
        .download-btn {
            background: rgba(0,0,0,0.15);
            border: none;
            border-radius: 5px;
            padding: 8px 15px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.2s;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-weight: bold;
        }
        .message-sent .download-btn {
            color: white;
            background: rgba(255,255,255,0.2);
        }
        .message-received .download-btn {
            color: #007bff;
            background: rgba(0,123,255,0.1);
        }
        .download-btn:hover {
            background: rgba(0,0,0,0.25);
            transform: scale(1.02);
        }
        .message-image {
            max-width: 250px;
            max-height: 250px;
            border-radius: 8px;
            margin-top: 5px;
            cursor: pointer;
            object-fit: cover;
        }
        .message-image:hover {
            opacity: 0.9;
        }
        .input-area {
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-top: 10px;
        }
        textarea {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
            font-family: inherit;
            resize: vertical;
            min-height: 80px;
            box-sizing: border-box;
        }
        .button-group {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        button {
            padding: 10px 20px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            flex: 1;
            transition: all 0.2s;
            font-weight: 500;
        }
        button:hover {
            background: #0056b3;
            transform: translateY(-1px);
        }
        .file-btn {
            background: #28a745;
        }
        .file-btn:hover {
            background: #1e7e34;
        }
        .status {
            padding: 8px;
            margin-bottom: 15px;
            border-radius: 6px;
            font-size: 12px;
            text-align: center;
        }
        .status-connected {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        #anyFileInput {
            display: none;
        }
        .preview-container {
            margin-top: 10px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 8px;
            display: none;
        }
        .preview-image {
            max-width: 150px;
            max-height: 150px;
            border-radius: 8px;
            display: block;
            margin-bottom: 10px;
        }
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.95);
        }
        .modal-content {
            margin: auto;
            display: block;
            max-width: 90%;
            max-height: 90%;
            margin-top: 50px;
        }
        .close {
            position: absolute;
            top: 15px;
            right: 35px;
            color: #f1f1f1;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
        }
        .toast {
            visibility: hidden;
            min-width: 250px;
            background-color: #333;
            color: #fff;
            text-align: center;
            border-radius: 8px;
            padding: 12px;
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 1001;
            font-size: 14px;
        }
        .toast.show {
            visibility: visible;
            animation: fadeInOut 2s;
        }
        @keyframes fadeInOut {
            0% { opacity: 0; bottom: 0; }
            10% { opacity: 1; bottom: 30px; }
            90% { opacity: 1; bottom: 30px; }
            100% { opacity: 0; bottom: 0; }
        }
        @media (max-width: 768px) {
            .message {
                max-width: 95%;
            }
            .button-group button {
                font-size: 12px;
                padding: 8px 12px;
            }
            .download-btn {
                padding: 10px 15px;
                font-size: 14px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h3><i class="fas fa-exchange-alt"></i> Two-Way File Sharing</h3>
            <p>Send & receive text, images, and any file type</p>
        </div>
        
        <div id="status" class="status status-connected">
            <i class="fas fa-circle" style="font-size: 10px; color: #28a745;"></i> Connected - Auto-refresh every 2 seconds
        </div>
        
        <div class="messages" id="messages">
            <div class="message message-system">
                <i class="fas fa-info-circle"></i> Welcome! You can send text or any file (images, documents, archives, etc.)
            </div>
        </div>
        
        <div class="input-area">
            <textarea id="messageInput" placeholder="Type your message here..."></textarea>
            <div class="button-group">
                <button onclick="sendMessage()"><i class="fas fa-paper-plane"></i> Send Text</button>
                <button class="file-btn" onclick="selectAnyFile()"><i class="fas fa-paperclip"></i> Send Any File</button>
            </div>
            <div id="filePreview" class="preview-container">
                <div id="filePreviewInfo"></div>
                <div style="margin-top: 8px;">
                    <button onclick="sendAnyFile()" style="background: #28a745; width: auto; padding: 5px 15px;"><i class="fas fa-upload"></i> Upload & Send</button>
                    <button onclick="cancelAnyFile()" style="background: #dc3545; width: auto; padding: 5px 15px;"><i class="fas fa-times"></i> Cancel</button>
                </div>
            </div>
        </div>
    </div>

    <div id="imageModal" class="modal">
        <span class="close" onclick="closeModal()">&times;</span>
        <img class="modal-content" id="modalImage">
    </div>

    <div id="toast" class="toast">✅ Copied to clipboard!</div>

    <input type="file" id="anyFileInput" onchange="previewAnyFile(event)">

    <script>
        let lastMessageCount = 0;
        let pendingFile = null;
        let pendingFileName = null;
        
        function selectAnyFile() {
            document.getElementById('anyFileInput').click();
        }
        
        function previewAnyFile(event) {
            const file = event.target.files[0];
            if (file) {
                pendingFile = file;
                pendingFileName = file.name;
                const fileSize = (file.size / 1024 / 1024).toFixed(2);
                const previewDiv = document.getElementById('filePreviewInfo');
                
                // Check if it's an image for preview
                if (file.type.startsWith('image/')) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        previewDiv.innerHTML = `
                            <img src="${e.target.result}" class="preview-image">
                            <div><strong>${escapeHtml(file.name)}</strong></div>
                            <div style="font-size: 12px; opacity: 0.7;">${fileSize} MB | Image file</div>
                        `;
                    };
                    reader.readAsDataURL(file);
                } else {
                    previewDiv.innerHTML = `
                        <i class="fas fa-file fa-3x"></i>
                        <div><strong>${escapeHtml(file.name)}</strong></div>
                        <div style="font-size: 12px; opacity: 0.7;">${fileSize} MB | ${file.type || 'Unknown type'}</div>
                    `;
                }
                document.getElementById('filePreview').style.display = 'block';
            }
        }
        
        function sendAnyFile() {
            if (pendingFile) {
                showToast('Uploading file...');
                const formData = new FormData();
                formData.append('file', pendingFile);
                formData.append('sender_type', 'system');
                
                fetch('/send_file', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        cancelAnyFile();
                        fetchMessages();
                        showToast('✅ File sent!');
                    } else {
                        showToast('❌ Failed to send file');
                    }
                })
                .catch(err => showToast('Error: ' + err));
            }
        }
        
        function cancelAnyFile() {
            pendingFile = null;
            pendingFileName = null;
            document.getElementById('filePreview').style.display = 'none';
            document.getElementById('anyFileInput').value = '';
        }
        
        function copyToClipboard(text) {
            // Create a temporary textarea element
            const textarea = document.createElement('textarea');
            textarea.value = text;
            document.body.appendChild(textarea);
            textarea.select();
            textarea.setSelectionRange(0, 99999);
            
            try {
                document.execCommand('copy');
                showToast('✅ Copied to clipboard!');
            } catch (err) {
                navigator.clipboard.writeText(text).then(() => {
                    showToast('✅ Copied to clipboard!');
                }).catch(() => {
                    showToast('❌ Failed to copy');
                });
            }
            
            document.body.removeChild(textarea);
        }
        
        function showToast(message) {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.className = 'toast show';
            setTimeout(() => {
                toast.className = 'toast';
            }, 2000);
        }
        
        function formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
        
        function getFileIcon(filename) {
            const ext = filename.split('.').pop().toLowerCase();
            const icons = {
                'pdf': 'fa-file-pdf',
                'doc': 'fa-file-word',
                'docx': 'fa-file-word',
                'xls': 'fa-file-excel',
                'xlsx': 'fa-file-excel',
                'zip': 'fa-file-archive',
                'rar': 'fa-file-archive',
                'json': 'fa-file-code',
                'txt': 'fa-file-alt',
                'jpg': 'fa-file-image',
                'jpeg': 'fa-file-image',
                'png': 'fa-file-image',
                'gif': 'fa-file-image',
                'mp4': 'fa-file-video',
                'mp3': 'fa-file-audio'
            };
            return icons[ext] || 'fa-file';
        }
        
        function fetchMessages() {
            fetch('/get_messages')
                .then(response => response.json())
                .then(data => {
                    if (JSON.stringify(data.messages) !== JSON.stringify(lastMessageCount)) {
                        updateMessages(data.messages);
                        lastMessageCount = data.messages;
                    }
                })
                .catch(err => console.log('Error fetching:', err));
        }
        
        function updateMessages(messagesList) {
            const messagesDiv = document.getElementById('messages');
            messagesDiv.innerHTML = '';
            
            messagesList.forEach(msg => {
                const messageDiv = document.createElement('div');
                const time = new Date(msg.timestamp).toLocaleTimeString();
                const isSystemSender = (msg.sender_type === 'system' && msg.sender === '{{ session_id }}');
                const alignment = isSystemSender ? 'sent' : 'received';
                const senderName = isSystemSender ? '<i class="fas fa-laptop"></i> You (System)' : '<i class="fas fa-mobile-alt"></i> Mobile';
                
                if (msg.type === 'file') {
                    messageDiv.className = alignment === 'sent' ? 'message message-sent' : 'message message-received';
                    
                    const fileIcon = getFileIcon(msg.file_name);
                    const isImage = msg.file_name.match(/\\.(jpg|jpeg|png|gif|bmp|webp)$/i);
                    
                    if (isImage) {
                        // Display image directly
                        const imageUrl = window.location.origin + msg.file_url;
                        messageDiv.innerHTML = `
                            <div class="device-name">${senderName} <i class="fas fa-image"></i></div>
                            <img src="${imageUrl}" class="message-image" onclick="showImage('${imageUrl}')">
                            <div class="file-name" style="font-size: 11px; margin-top: 5px;">${escapeHtml(msg.file_name)}</div>
                            <div class="message-time">${time}</div>
                            <a href="${imageUrl}" download="${escapeHtml(msg.file_name)}" class="download-btn" style="margin-top: 5px;">
                                <i class="fas fa-download"></i> Download Image
                            </a>
                        `;
                    } else {
                        // Display as file
                        const downloadUrl = window.location.origin + msg.file_url;
                        messageDiv.innerHTML = `
                            <div class="device-name">${senderName}</div>
                            <div class="file-info">
                                <i class="fas ${fileIcon} file-icon"></i>
                                <div class="file-details">
                                    <div class="file-name">${escapeHtml(msg.file_name)}</div>
                                    <div class="file-size">${formatFileSize(msg.file_size)}</div>
                                </div>
                                <a href="${downloadUrl}" download="${escapeHtml(msg.file_name)}" class="download-btn">
                                    <i class="fas fa-download"></i> Download
                                </a>
                            </div>
                            <div class="message-time">${time}</div>
                        `;
                    }
                } 
                else {
                    // Text message
                    messageDiv.className = alignment === 'sent' ? 'message message-sent' : 'message message-received';
                    
                    const textContent = escapeHtml(msg.text);
                    const copyButton = !isSystemSender ? `<div><button class="copy-btn" onclick="copyToClipboard(\`${msg.text.replace(/`/g, '\\\\`').replace(/\\$/g, '\\\\$')}\`)"><i class="fas fa-copy"></i> Copy Text</button></div>` : '';
                    
                    messageDiv.innerHTML = `
                        <div class="device-name">${senderName}</div>
                        <div style="word-wrap: break-word;">${textContent}</div>
                        <div class="message-time">${time}</div>
                        ${copyButton}
                    `;
                }
                
                messagesDiv.appendChild(messageDiv);
            });
            
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function sendMessage() {
            const input = document.getElementById('messageInput');
            const text = input.value.trim();
            
            if (text === '') {
                showToast('Please enter a message');
                return;
            }
            
            fetch('/send_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    sender_type: 'system'
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    input.value = '';
                    fetchMessages();
                    showToast('✅ Message sent!');
                } else {
                    showToast('❌ Failed to send message');
                }
            })
            .catch(err => showToast('Error: ' + err));
        }
        
        function showImage(url) {
            const modal = document.getElementById('imageModal');
            const modalImg = document.getElementById('modalImage');
            modal.style.display = "block";
            modalImg.src = url;
        }
        
        function closeModal() {
            document.getElementById('imageModal').style.display = "none";
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Auto-refresh
        fetchMessages();
        setInterval(fetchMessages, 2000);
        
        // Enter key to send
        document.getElementById('messageInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        // Close modal with ESC
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeModal();
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    import uuid
    session_id = request.cookies.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
    
    response = app.make_response(render_template_string(HTML_TEMPLATE, session_id=session_id))
    response.set_cookie('session_id', session_id)
    return response

@app.route('/send_message', methods=['POST'])
def send_message():
    global messages, last_id
    data = request.json
    session_id = request.cookies.get('session_id', 'unknown')
    
    message = {
        'id': last_id,
        'type': 'text',
        'text': data['text'],
        'sender': session_id,
        'sender_type': data['sender_type'],
        'timestamp': datetime.now().isoformat()
    }
    
    messages.append(message)
    last_id += 1
    
    if len(messages) > 200:
        messages = messages[-200:]
    
    return jsonify({'success': True, 'id': last_id - 1})

@app.route('/send_file', methods=['POST'])
def send_file():
    global messages, last_id
    session_id = request.cookies.get('session_id', 'unknown')
    sender_type = request.form.get('sender_type', 'system')
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    # Generate unique filename
    original_filename = file.filename
    file_ext = os.path.splitext(original_filename)[1]
    safe_filename = f"file_{uuid.uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    # Save file
    file.save(file_path)
    file_size = os.path.getsize(file_path)
    
    message = {
        'id': last_id,
        'type': 'file',
        'file_name': original_filename,
        'file_size': file_size,
        'file_url': f'/get_file/{safe_filename}',
        'sender': session_id,
        'sender_type': sender_type,
        'timestamp': datetime.now().isoformat()
    }
    
    messages.append(message)
    last_id += 1
    
    if len(messages) > 200:
        messages = messages[-200:]
    
    return jsonify({'success': True, 'id': last_id - 1, 'file_name': original_filename})

@app.route('/get_file/<filename>')
def get_file(filename):
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    # Find original filename from messages
    original_filename = filename
    for msg in messages:
        if msg.get('type') == 'file' and msg.get('file_url', '').endswith(filename):
            original_filename = msg.get('file_name')
            break
    
    # Get file extension and set proper headers for mobile
    file_ext = os.path.splitext(original_filename)[1].lower()
    
    # Create response with forced download headers for mobile
    with open(file_path, 'rb') as f:
        file_data = f.read()
    
    response = Response(file_data)
    response.headers['Content-Type'] = 'application/octet-stream'
    response.headers['Content-Disposition'] = f'attachment; filename="{original_filename}"'
    response.headers['Content-Length'] = len(file_data)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

@app.route('/get_messages')
def get_messages():
    return jsonify({'messages': messages})

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

if __name__ == '__main__':
    ip = get_local_ip()
    port = 5000
    
    print("\n" + "="*70)
    print("🚀 TWO-WAY FILE SHARING - MOBILE OPTIMIZED")
    print("="*70)
    print(f"\n📱 Mobile access URL:")
    print(f"   http://{ip}:{port}")
    print(f"\n💻 Computer access URL:")
    print(f"   http://localhost:{port}")
    print("\n" + "="*70)
    print("✨ FEATURES:")
    print("   • Send any file type (images, documents, zip, etc.)")
    print("   • Images displayed directly in chat")
    print("   • Copy button for text messages")
    print("   • No file size limit")
    print("   • Optimized for mobile download")
    print("   • English interface")
    print("\n⛔ Stop server: Ctrl+C")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
