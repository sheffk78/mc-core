import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api/v1`;

const api = axios.create({
  baseURL: API,
  headers: { 'Content-Type': 'application/json' },
});

export const fetchBrands = () => api.get('/brands').then(r => r.data);
export const fetchStats = (brand) => api.get('/stats', { params: { brand } }).then(r => r.data);
export const fetchApprovals = (brand, status = 'pending', search = '') => {
  const params = { brand, status };
  if (search && search.trim()) params.search = search.trim();
  return api.get('/approvals', { params }).then(r => r.data);
};
export const approveItem = (id) => api.post(`/approvals/${id}/approve`).then(r => r.data);
export const rejectItem = (id) => api.post(`/approvals/${id}/reject`).then(r => r.data);
export const discardItem = (id) => api.post(`/approvals/${id}/discard`).then(r => r.data);
export const fetchAgents = (brand) => api.get('/agents', { params: { brand } }).then(r => r.data);
export const fetchTasks = (brand, assignee) => {
  const params = { brand };
  if (assignee && assignee !== 'all') params.assignee = assignee;
  return api.get('/tasks', { params }).then(r => r.data);
};
export const createTask = (data) => api.post('/tasks', data).then(r => r.data);
export const completeTask = (id) => api.post(`/tasks/${id}/complete`).then(r => r.data);
export const reopenTask = (id) => api.post(`/tasks/${id}/reopen`).then(r => r.data);
export const updateTaskStatus = (id, status) => api.patch(`/tasks/${id}/status`, { status }).then(r => r.data);
export const updateTask = (id, data) => api.patch(`/tasks/${id}`, data).then(r => r.data);
export const deferTask = (id, due_date, reason) => api.post(`/tasks/${id}/defer`, { due_date, reason }).then(r => r.data);
export const redirectTask = (id, note, priority) => api.post(`/tasks/${id}/redirect`, { note, priority }).then(r => r.data);
export const deleteTask = (id) => api.delete(`/tasks/${id}`).then(r => r.data);
export const fetchInboxes = (brand) => api.get('/inboxes', { params: { brand } }).then(r => r.data);
export const fetchAgentMailInboxes = (brand) => api.get('/agentmail/inboxes', { params: { brand } }).then(r => r.data);
export const fetchAgentMailMessages = (inboxId, limit = 20, labels = null) => {
  const params = { limit };
  if (labels) params.labels = labels;
  return api.get(`/agentmail/inboxes/${encodeURIComponent(inboxId)}/messages`, { params }).then(r => r.data);
};
export const updateMessageLabels = (inboxId, messageId, addLabels = [], removeLabels = []) =>
  api.post(`/agentmail/inboxes/${encodeURIComponent(inboxId)}/messages/${encodeURIComponent(messageId)}/labels`, { add_labels: addLabels, remove_labels: removeLabels }).then(r => r.data);
export const fetchAgentMailThread = (threadId) => api.get(`/agentmail/threads/${threadId}`).then(r => r.data);
export const composeEmail = (data) => api.post('/agentmail/compose', data).then(r => r.data);
export const replyToMessage = (inboxId, messageId, data) => api.post(`/agentmail/reply/${encodeURIComponent(inboxId)}/${encodeURIComponent(messageId)}`, data).then(r => r.data);
export const registerWebhook = () => api.post('/agentmail/webhooks/register').then(r => r.data);
export const listWebhooks = () => api.get('/agentmail/webhooks').then(r => r.data);
export const fetchCalendarFeeds = () => api.get('/calendar/feeds').then(r => r.data);
export const addCalendarFeed = (data) => api.post('/calendar/feeds', data).then(r => r.data);
export const deleteCalendarFeed = (id) => api.delete(`/calendar/feeds/${id}`).then(r => r.data);
export const fetchCalendarEvents = (daysAhead = 30, daysBehind = 7) => api.get('/calendar/events', { params: { days_ahead: daysAhead, days_behind: daysBehind } }).then(r => r.data);

// Google Calendar OAuth
export const getCalendarOAuthUrl = () => api.get('/oauth/calendar/login').then(r => r.data);
export const getCalendarConnectionStatus = () => api.get('/oauth/calendar/status').then(r => r.data);
export const disconnectCalendarAccount = (id) => api.delete(`/oauth/calendar/disconnect/${id}`).then(r => r.data);
export const createCalendarEvent = (data) => api.post('/calendar/events', data).then(r => r.data);
export const updateCalendarEvent = (eventId, data) => api.put(`/calendar/events/${eventId}`, data).then(r => r.data);
export const deleteCalendarEvent = (eventId, calendarId = 'primary') => api.delete(`/calendar/events/${eventId}`, { params: { calendar_id: calendarId } }).then(r => r.data);
export const fetchActivity = (brand, limit = 20) => api.get('/activity', { params: { brand, limit } }).then(r => r.data);
export const syncAgentMail = () => api.post('/agentmail/sync').then(r => r.data);
export const seedDatabase = () => api.post('/seed').then(r => r.data);
export const fetchTemplates = () => api.get('/templates').then(r => r.data);
export const createTemplate = (data) => api.post('/templates', data).then(r => r.data);
export const deleteTemplate = (id) => api.delete(`/templates/${id}`).then(r => r.data);

// Schedule (Cron Jobs)
export const fetchWeeklySchedule = (weekOffset = 0) => api.get('/schedule/weekly', { params: { week_offset: weekOffset } }).then(r => r.data);
export const fetchSchedule = (brand) => api.get('/schedule', { params: { brand } }).then(r => r.data);
export const createScheduleItem = (data) => api.post('/schedule', data).then(r => r.data);
export const pauseSchedule = (id) => api.post(`/schedule/${id}/pause`).then(r => r.data);
export const resumeSchedule = (id) => api.post(`/schedule/${id}/resume`).then(r => r.data);
export const runScheduleNow = (id) => api.post(`/schedule/${id}/run-now`).then(r => r.data);
export const editSchedule = (id, data) => api.post(`/schedule/${id}/edit`, data).then(r => r.data);
export const deleteScheduleItem = (id) => api.delete(`/schedule/${id}`).then(r => r.data);

// Users
export const fetchUsers = () => api.get('/users').then(r => r.data);
export const createUser = (data) => api.post('/users', data).then(r => r.data);
export const updateUser = (id, data) => api.patch(`/users/${id}`, data).then(r => r.data);
export const deleteUser = (id) => api.delete(`/users/${id}`).then(r => r.data);

// Brand management
export const createBrand = (data) => api.post('/brands', data).then(r => r.data);
export const updateBrand = (slug, data) => api.patch(`/brands/${slug}`, data).then(r => r.data);
export const deleteBrand = (slug) => api.delete(`/brands/${slug}`).then(r => r.data);

// Morning Briefs
export const fetchMorningBrief = (brand) => api.get(`/briefs/${encodeURIComponent(brand)}`).then(r => r.data);
