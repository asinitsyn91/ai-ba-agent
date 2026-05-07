const API_BASE = window.API_BASE || `http://${window.location.hostname}:8000/api/v1`;

export async function analyze(text, projectName = 'tbd') {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, project_name: projectName }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function clarify(sessionId, answers) {
  const res = await fetch(`${API_BASE}/clarify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, answers }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function finalize(sessionId) {
  const res = await fetch(`${API_BASE}/finalize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
