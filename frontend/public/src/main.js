import { analyze, clarify, finalize } from './api/client.js';

let state = {
  sessionId: null,
  requirements: [],
  questions: [],
  status: null,
};

function render() {
  const app = document.getElementById('app');
  app.innerHTML = `
    <header>
      <h1>🤖 AI-ba-agent</h1>
      <p class="subtitle">Бизнес-аналитик · Корпоративный архитектор</p>
    </header>
    <main>
      ${state.sessionId ? renderWorkspace() : renderInput()}
    </main>
  `;
  bindEvents();
}

function renderInput() {
  return `
    <section class="card input-section">
      <h2>Введите исходные данные</h2>
      <div class="form-group">
        <label for="project-name">Название проекта</label>
        <input id="project-name" type="text" placeholder="Например: CRM-система" value="" />
      </div>
      <div class="form-group">
        <label for="source-text">Текст (протокол встречи, письмо, интервью)</label>
        <textarea id="source-text" rows="12" placeholder="Вставьте неструктурированный текст с бизнес-потребностями заказчика..."></textarea>
      </div>
      <button id="btn-analyze" class="btn btn-primary">Извлечь требования</button>
      <div id="error-msg" class="error hidden"></div>
      <div id="loading" class="loading hidden">⏳ Анализ... это может занять 1-2 минуты</div>
    </section>
  `;
}

function renderWorkspace() {
  return `
    <div class="workspace">
      <div class="workspace-header">
        <button id="btn-reset" class="btn btn-secondary">← Новый анализ</button>
        <span class="status-badge status-${state.status}">${statusLabel(state.status)}</span>
      </div>

      ${state.questions.length > 0 ? renderQuestions() : ''}

      <section class="card">
        <h2>Требования (${state.requirements.length})</h2>
        <div class="table-wrap">
          <table class="req-table">
            <thead>
              <tr>
                <th>ID</th><th>Тип</th><th>Описание (EARS)</th>
                <th>Fit Criterion</th><th>Приоритет</th><th>Статус</th>
              </tr>
            </thead>
            <tbody>
              ${state.requirements.map(r => `
                <tr class="priority-${r.priority}">
                  <td><code>${r.req_id}</code></td>
                  <td><span class="type-badge">${r.req_type}</span></td>
                  <td>${r.description}</td>
                  <td class="fit">${r.fit_criterion || '—'}</td>
                  <td>${r.priority || 'tbd'}</td>
                  <td>${r.status}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      </section>

      ${state.qualityCheck ? renderQuality() : ''}

      <div class="actions">
        <button id="btn-finalize" class="btn btn-primary" ${state.status === 'needs_clarification' ? 'disabled title="Ответьте на вопросы перед финализацией"' : ''}>
          Сформировать Volere JSON
        </button>
      </div>

      <div id="final-output" class="hidden"></div>
      <div id="error-msg" class="error hidden"></div>
    </div>
  `;
}

function renderQuestions() {
  return `
    <section class="card questions-section">
      <h2>❓ Уточняющие вопросы (${state.questions.length})</h2>
      <p class="hint">Ответьте на вопросы для уточнения требований. Оставьте поле пустым, чтобы пропустить.</p>
      ${state.questions.map((q, i) => `
        <div class="question-item">
          <div class="q-header">
            <span class="q-id">${q.id}</span>
            <span class="priority-badge priority-${q.priority}">${q.priority}</span>
            <span class="q-ref">→ ${q.ref}</span>
          </div>
          <p class="q-text">${q.text}</p>
          ${q.why ? `<p class="q-why"><em>Почему важно:</em> ${q.why}</p>` : ''}
          ${q.options?.length ? `<p class="q-options"><em>Варианты:</em> ${q.options.join(' | ')}</p>` : ''}
          <textarea class="q-answer" data-qid="${q.id}" rows="2" placeholder="Ваш ответ..."></textarea>
        </div>
      `).join('')}
      <button id="btn-clarify" class="btn btn-secondary">Применить ответы</button>
    </section>
  `;
}

function renderQuality() {
  const q = state.qualityCheck;
  const issues = q.quality_issues || [];
  const gaps = q.gaps || [];
  const conflicts = q.conflicts || [];
  if (!issues.length && !gaps.length && !conflicts.length) return '';
  return `
    <section class="card quality-section">
      <h2>🔍 Качество требований (BABOK)</h2>
      ${issues.length ? `
        <h3>Нарушения (${issues.length})</h3>
        <ul>${issues.map(i => `<li><code>${i.req_id}</code> · <strong>${i.attribute}</strong>: ${i.issue}</li>`).join('')}</ul>
      ` : ''}
      ${conflicts.length ? `
        <h3>Конфликты (${conflicts.length})</h3>
        <ul>${conflicts.map(c => `<li>${c.req_ids?.join(', ')} — ${c.description}</li>`).join('')}</ul>
      ` : ''}
      ${gaps.length ? `
        <h3>Пробелы в покрытии</h3>
        <ul>${gaps.map(g => `<li>${g}</li>`).join('')}</ul>
      ` : ''}
    </section>
  `;
}

function statusLabel(s) {
  return s === 'needs_clarification' ? 'Требуют уточнения' : s === 'ready' ? 'Готово к финализации' : s;
}

function setLoading(show) {
  const el = document.getElementById('loading');
  if (el) el.classList.toggle('hidden', !show);
}

function showError(msg) {
  const el = document.getElementById('error-msg');
  if (el) { el.textContent = msg; el.classList.remove('hidden'); }
}

function bindEvents() {
  document.getElementById('btn-analyze')?.addEventListener('click', async () => {
    const text = document.getElementById('source-text').value.trim();
    const projectName = document.getElementById('project-name').value.trim() || 'tbd';
    if (!text) { showError('Введите текст для анализа'); return; }
    document.getElementById('btn-analyze').disabled = true;
    setLoading(true);
    try {
      const res = await analyze(text, projectName);
      state = { sessionId: res.session_id, requirements: res.requirements,
                questions: res.questions, status: res.status, qualityCheck: res.quality_check };
      render();
    } catch (e) {
      showError('Ошибка: ' + e.message);
      document.getElementById('btn-analyze').disabled = false;
      setLoading(false);
    }
  });

  document.getElementById('btn-reset')?.addEventListener('click', () => {
    state = { sessionId: null, requirements: [], questions: [], status: null };
    render();
  });

  document.getElementById('btn-clarify')?.addEventListener('click', async () => {
    const answers = state.questions.map(q => {
      const ans = document.querySelector(`.q-answer[data-qid="${q.id}"]`)?.value?.trim();
      return ans ? `${q.id}: ${ans}` : null;
    }).filter(Boolean).join('\n');

    if (!answers) { showError('Введите хотя бы один ответ'); return; }
    document.getElementById('btn-clarify').disabled = true;
    try {
      const res = await clarify(state.sessionId, answers);
      state.requirements = res.requirements;
      state.questions = res.questions;
      state.status = res.status;
      state.qualityCheck = res.quality_check;
      render();
    } catch (e) {
      showError('Ошибка: ' + e.message);
      document.getElementById('btn-clarify').disabled = false;
    }
  });

  document.getElementById('btn-finalize')?.addEventListener('click', async () => {
    document.getElementById('btn-finalize').disabled = true;
    try {
      const res = await finalize(state.sessionId);
      const out = document.getElementById('final-output');
      out.classList.remove('hidden');
      out.innerHTML = `
        <section class="card">
          <h2>✅ Volere JSON сформирован</h2>
          <div class="summary">
            <strong>Итого требований:</strong> ${res.summary.total} |
            <strong>Открытых вопросов:</strong> ${res.summary.open_questions} |
            <strong>Проблем качества:</strong> ${res.summary.quality_issues}
          </div>
          <div class="download-bar">
            <button id="btn-download" class="btn btn-primary">⬇ Скачать JSON</button>
          </div>
          <pre class="json-preview">${JSON.stringify(res.volere_json, null, 2)}</pre>
        </section>
      `;
      document.getElementById('btn-download').addEventListener('click', () => {
        const blob = new Blob([JSON.stringify(res.volere_json, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = `requirements_${state.sessionId?.slice(0,8)}.json`; a.click();
      });
    } catch (e) {
      showError('Ошибка: ' + e.message);
      document.getElementById('btn-finalize').disabled = false;
    }
  });
}

render();
