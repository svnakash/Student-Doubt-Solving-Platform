const API_BASE = 'http://127.0.0.1:5000/api/v1';

const state = {
  token: localStorage.getItem('campusq_token') || '',
  user: null,
  questions: [],
  selectedQuestionId: null,
  currentView: 'auth',
};

const elements = {
  authView: document.getElementById('auth-view'),
  dashboardView: document.getElementById('dashboard-view'),
  questionsView: document.getElementById('questions-view'),
  detailView: document.getElementById('detail-view'),
  userBadge: document.getElementById('user-badge'),
  logoutBtn: document.getElementById('logout-btn'),
  loginForm: document.getElementById('login-form'),
  registerForm: document.getElementById('register-form'),
  verificationForm: document.getElementById('verification-form'),
  questionForm: document.getElementById('question-form'),
  questionList: document.getElementById('questions-list'),
  detailContent: document.getElementById('detail-content'),
  verificationStatus: document.getElementById('verification-status'),
  userRole: document.getElementById('user-role'),
  questionCount: document.getElementById('question-count'),
  verificationMessage: document.getElementById('verification-message'),
  questionMessage: document.getElementById('question-message'),
  navHome: document.getElementById('nav-home'),
  navDashboard: document.getElementById('nav-dashboard'),
  navQuestions: document.getElementById('nav-questions'),
  backToQuestions: document.getElementById('back-to-questions'),
  refreshQuestions: document.getElementById('refresh-questions'),
};

function setMessage(element, type, text) {
  element.textContent = text || '';
  element.className = `message-box ${type}`;
}

function showView(view) {
  state.currentView = view;
  elements.authView.classList.toggle('hidden', view !== 'auth');
  elements.dashboardView.classList.toggle('hidden', view !== 'dashboard');
  elements.questionsView.classList.toggle('hidden', view !== 'questions');
  elements.detailView.classList.toggle('hidden', view !== 'detail');

  elements.navHome.classList.toggle('active', view === 'auth');
  elements.navDashboard.classList.toggle('active', view === 'dashboard');
  elements.navQuestions.classList.toggle('active', view === 'questions' || view === 'detail');
}

function updateAuthUI() {
  if (state.token) {
    elements.userBadge.textContent = state.user ? state.user.name : 'Logged in';
    elements.userBadge.classList.remove('hidden');
    elements.logoutBtn.classList.remove('hidden');
  } else {
    elements.userBadge.textContent = 'Guest';
    elements.userBadge.classList.add('hidden');
    elements.logoutBtn.classList.add('hidden');
  }
}

function persistToken(token) {
  state.token = token;
  if (token) {
    localStorage.setItem('campusq_token', token);
  } else {
    localStorage.removeItem('campusq_token');
  }
  updateAuthUI();
}

async function apiFetch(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload?.error?.message || 'Request failed');
  }

  return payload;
}

async function loadCurrentUser() {
  if (!state.token) {
    showView('auth');
    return;
  }

  try {
    const result = await apiFetch('/auth/me');
    state.user = result.data;
    updateAuthUI();
    showView('dashboard');
    renderUserSummary();
    await loadQuestions();
  } catch (error) {
    persistToken('');
    state.user = null;
    showView('auth');
  }
}

function renderUserSummary() {
  if (!state.user) {
    elements.verificationStatus.textContent = 'Pending';
    elements.userRole.textContent = 'Guest';
    elements.questionCount.textContent = '0';
    return;
  }

  elements.verificationStatus.textContent = state.user.verification_status || 'Pending';
  elements.userRole.textContent = state.user.role || 'student';
}

async function registerUser(event) {
  event.preventDefault();
  const name = document.getElementById('register-name').value.trim();
  const email = document.getElementById('register-email').value.trim();
  const password = document.getElementById('register-password').value;

  try {
    const result = await apiFetch('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    });

    if (result.success) {
      document.getElementById('register-form').reset();
      document.querySelector('[data-form-toggle="login-card"]').click();
      setMessage(elements.questionMessage, 'success', 'Account created. Please log in.');
    }
  } catch (error) {
    setMessage(elements.questionMessage, 'error', error.message);
  }
}

async function loginUser(event) {
  event.preventDefault();
  const email = document.getElementById('login-email').value.trim();
  const password = document.getElementById('login-password').value;

  try {
    const result = await apiFetch('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });

    persistToken(result.data.access_token);
    state.user = result.data.user;
    renderUserSummary();
    document.getElementById('login-form').reset();
    await loadCurrentUser();
  } catch (error) {
    setMessage(elements.questionMessage, 'error', error.message);
  }
}

function logout() {
  persistToken('');
  state.user = null;
  state.questions = [];
  state.selectedQuestionId = null;
  elements.questionList.innerHTML = '';
  elements.detailContent.innerHTML = '';
  showView('auth');
}

async function uploadIDCard(event) {
  event.preventDefault();
  const fileInput = document.getElementById('id-card-file');
  const file = fileInput.files[0];

  if (!file) {
    setMessage(elements.verificationMessage, 'error', 'Please select an image first.');
    return;
  }

  const formData = new FormData();
  formData.append('id_card', file);

  try {
    const result = await fetch(`${API_BASE}/verification/upload`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${state.token}`,
      },
      body: formData,
    });

    const payload = await result.json().catch(() => ({}));
    if (!result.ok) {
      throw new Error(payload?.error?.message || 'Verification failed');
    }

    setMessage(elements.verificationMessage, 'success', 'Verification successful.');
    await loadCurrentUser();
  } catch (error) {
    setMessage(elements.verificationMessage, 'error', error.message);
  }
}

async function createQuestion(event) {
  event.preventDefault();
  const subject = document.getElementById('question-subject').value.trim();
  const title = document.getElementById('question-title').value.trim();
  const body = document.getElementById('question-body').value.trim();

  try {
    const result = await apiFetch('/questions/', {
      method: 'POST',
      body: JSON.stringify({ subject, title, body }),
    });

    document.getElementById('question-form').reset();
    setMessage(elements.questionMessage, 'success', 'Question submitted successfully.');
    await loadQuestions();
    showView('questions');
  } catch (error) {
    setMessage(elements.questionMessage, 'error', error.message);
  }
}

async function loadQuestions() {
  if (!state.token) {
    return;
  }

  try {
    const result = await apiFetch('/questions/');
    state.questions = result.data || [];
    elements.questionCount.textContent = String(state.questions.length);
    renderQuestionList();
  } catch (error) {
    elements.questionList.innerHTML = `<div class="empty-state">${error.message}</div>`;
  }
}

function renderQuestionList() {
  if (!state.questions.length) {
    elements.questionList.innerHTML = '<div class="empty-state">No questions yet.</div>';
    return;
  }

  elements.questionList.innerHTML = state.questions
    .map(
      (q) => `
        <article class="question-item">
          <h4>${escapeHtml(q.title)}</h4>
          <div class="meta-line">${escapeHtml(q.subject)} • ${new Date(q.created_at).toLocaleDateString()}</div>
          <p>${escapeHtml(q.body.slice(0, 180))}${q.body.length > 180 ? '...' : ''}</p>
          <div class="question-footer">
            <span class="badge">${q.status}</span>
            <button class="secondary-btn small-btn" data-open-question="${q.id}">Open</button>
          </div>
        </article>
      `
    )
    .join('');

  document.querySelectorAll('[data-open-question]').forEach((btn) => {
    btn.addEventListener('click', () => openQuestion(Number(btn.dataset.openQuestion)));
  });
}

async function openQuestion(questionId) {
  state.selectedQuestionId = questionId;
  try {
    const [questionResult, answersResult] = await Promise.all([
      apiFetch(`/questions/${questionId}`),
      apiFetch(`/questions/${questionId}/answers`),
    ]);

    const question = questionResult.data;
    question.answers = answersResult.data || [];
    renderQuestionDetail(question);
    showView('detail');
  } catch (error) {
    setMessage(elements.questionMessage, 'error', error.message);
  }
}

function renderQuestionDetail(question) {
  const answers = question.answers || [];
  document.getElementById('detail-title').textContent = question.title;

  const canAnswer = state.user && state.user.role === 'faculty' && state.user.verification_status === 'verified';

  const answerList = answers.length
    ? answers
        .map(
          (answer) => `
            <div class="answer-box">
              <strong>Faculty answer</strong>
              <p>${escapeHtml(answer.body)}</p>
            </div>
          `
        )
        .join('')
    : '<div class="empty-state">No answers yet.</div>';

  const answerForm = canAnswer
    ? `
      <form id="answer-form" class="stacked-form">
        <label>
          Your answer
          <textarea id="answer-body" rows="5" required></textarea>
        </label>
        <button type="submit" class="primary-btn">Submit answer</button>
      </form>
      <div id="answer-message" class="message-box"></div>
    `
    : '';

  elements.detailContent.innerHTML = `
    <div class="question-box">
      <div class="meta-line">${escapeHtml(question.subject)} • ${new Date(question.created_at).toLocaleDateString()}</div>
      <p>${escapeHtml(question.body)}</p>
      <span class="badge">${question.status}</span>
    </div>

    ${question.ai_answer ? `<div class="question-box"><strong>AI answer</strong><p>${escapeHtml(question.ai_answer)}</p></div>` : ''}

    <div class="answer-box">
      <strong>Answers</strong>
      ${answerList}
    </div>

    ${answerForm}
  `;

  const form = document.getElementById('answer-form');
  if (form) {
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const body = document.getElementById('answer-body').value.trim();
      try {
        await apiFetch(`/questions/${question.id}/answers`, {
          method: 'POST',
          body: JSON.stringify({ body }),
        });
        const message = document.getElementById('answer-message');
        setMessage(message, 'success', 'Answer submitted successfully.');
        openQuestion(question.id);
      } catch (error) {
        const message = document.getElementById('answer-message');
        setMessage(message, 'error', error.message);
      }
    });
  }
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function wireEvents() {
  document.querySelectorAll('[data-form-toggle]').forEach((button) => {
    button.addEventListener('click', () => {
      document.querySelectorAll('.form-card').forEach((card) => {
        card.classList.toggle('active', card.id === button.dataset.formToggle);
      });
      document.querySelectorAll('.link-btn').forEach((link) => {
        link.classList.toggle('active', link.dataset.formToggle === button.dataset.formToggle);
      });
    });
  });

  elements.loginForm.addEventListener('submit', loginUser);
  elements.registerForm.addEventListener('submit', registerUser);
  elements.verificationForm.addEventListener('submit', uploadIDCard);
  elements.questionForm.addEventListener('submit', createQuestion);
  elements.logoutBtn.addEventListener('click', logout);
  elements.navDashboard.addEventListener('click', () => {
    if (state.token) showView('dashboard');
  });
  elements.navQuestions.addEventListener('click', () => {
    if (state.token) {
      showView('questions');
      loadQuestions();
    }
  });
  elements.navHome.addEventListener('click', () => {
    showView(state.token ? 'dashboard' : 'auth');
  });
  elements.backToQuestions.addEventListener('click', () => {
    showView('questions');
  });
  elements.refreshQuestions.addEventListener('click', () => loadQuestions());
}

async function init() {
  wireEvents();
  updateAuthUI();
  showView('auth');

  if (state.token) {
    await loadCurrentUser();
  }
}

init();
