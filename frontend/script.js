let sessionId = null;
let isProcessing = false;
let downloadUrl = null;

const chatHistory = document.getElementById('chatHistory');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const optionsContainer = document.getElementById('optionsContainer');
const courseInfo = document.getElementById('courseInfo');

window.addEventListener('load', startSession);
sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') sendMessage();
});

async function startSession() {
    try {
        const res = await fetch('http://127.0.0.1:5000/api/start_session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        sessionId = data.session_id;
        addMessage('consultant', data.message);
        addMessage('consultant', data.next_prompt);
        userInput.focus();
    } catch (err) {
        console.error('启动失败:', err);
        addMessage('consultant', '系统错误，请刷新页面重试。');
    }
}

async function sendMessage() {
    if (isProcessing || !userInput.value.trim()) return;

    const message = userInput.value.trim();
    userInput.value = '';
    addMessage('user', message);
    optionsContainer.innerHTML = '';
    isProcessing = true;
    sendBtn.disabled = true;

    try {
        const res = await fetch('http://127.0.0.1:5000/api/interact', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, user_input: message })
        });
        const data = await res.json();

        if (data.message) addMessage('consultant', data.message);
        if (data.next_prompt) addMessage('consultant', data.next_prompt);
        if (data.options) showOptions(data.options);
        if (data.course_title) showCourseInfo(data); // 直接显示课程信息
        if (data.download_url) downloadUrl = data.download_url;
        if (data.error) addMessage('consultant', data.error); // 显示详细错误

    } catch (err) {
        console.error('发送失败:', err);
        addMessage('consultant', '系统错误，请重试。');
    } finally {
        isProcessing = false;
        sendBtn.disabled = false;
        userInput.focus();
    }
}

async function generateCourse() {
    try {
        const res = await fetch(`http://127.0.0.1:5000/api/generate_course/${sessionId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        removeLoading();
        if (data.message) addMessage('consultant', data.message);
        if (data.course_title) showCourseInfo(data);
        if (data.download_url) downloadUrl = data.download_url;
    } catch (err) {
        console.error('生成失败:', err);
        removeLoading();
        addMessage('consultant', '生成课程失败，请重试。');
    } finally {
        isProcessing = false;
        sendBtn.disabled = false;
    }
}

function addMessage(type, content) {
    const msg = document.createElement('div');
    msg.className = `message ${type}`;
    msg.textContent = content;
    chatHistory.appendChild(msg);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function showOptions(options) {
    optionsContainer.innerHTML = '';
    options.forEach(option => {
        const btn = document.createElement('button');
        btn.className = 'option-btn';
        btn.textContent = option;
        btn.addEventListener('click', () => {
            userInput.value = option;
            sendMessage();
        });
        optionsContainer.appendChild(btn);
    });
}

function showLoading(text) {
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading';
    loadingDiv.id = 'loadingIndicator';

    const spinner = document.createElement('div');
    spinner.className = 'loading-spinner';
    const span = document.createElement('span');
    span.textContent = text;

    loadingDiv.append(spinner, span);
    chatHistory.appendChild(loadingDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function removeLoading() {
    const loading = document.getElementById('loadingIndicator');
    if (loading) loading.remove();
}

function showCourseInfo(data) {
    courseInfo.style.display = 'block';
    courseInfo.innerHTML = `
        <h3>课程生成成功</h3>
        <p><strong>课程标题:</strong> ${data.course_title}</p>
        <p><strong>章节数量:</strong> ${data.chapter_count}</p>
        <a href="${data.download_url}" class="download-btn" target="_blank">下载课程包</a>
    `;
}