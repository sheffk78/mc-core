import { create } from 'zustand';
import { api } from '../lib/api';
import { subscribe } from '../lib/ws';

// ── Types ──

export interface ChatChannel {
  discord_channel_id: string;
  name: string;
  slug: string;
  brand_id: string | null;
  last_message_at: string | null;
  unread_count: number;
  brand_color?: string;
}

export interface ChatMessage {
  id: string;
  channel_id: string;
  channel_slug: string;
  discord_message_id: string | null;
  discord_author_id: string | null;
  discord_author_name: string;
  discord_author_avatar: string | null;
  content: string;
  is_from_kit: number;
  is_read: number;
  created_at: string;
}

// ── TTS Preferences ──

interface TTSPrefs {
  voiceIndex: number;
  rate: number;
  autoRead: boolean;
}

const TTS_STORAGE_KEY = 'mc_tts_prefs';

function loadTTSPrefs(): TTSPrefs {
  try {
    const stored = localStorage.getItem(TTS_STORAGE_KEY);
    if (stored) return JSON.parse(stored);
  } catch {}
  return { voiceIndex: 0, rate: 1, autoRead: false };
}

function saveTTSPrefs(prefs: TTSPrefs): void {
  try {
    localStorage.setItem(TTS_STORAGE_KEY, JSON.stringify(prefs));
  } catch {}
}

// ── State ──

interface ChatState {
  channels: ChatChannel[];
  messages: Record<string, ChatMessage[]>; // keyed by channel_id
  activeChannel: string | null;
  loading: Partial<Record<'channels' | 'messages' | 'sending', boolean>>;
  sending: boolean;
  error: string | null;

  // TTS
  ttsEnabled: boolean;
  ttsSpeaking: boolean;
  ttsCurrentMessageId: string | null;
  ttsVoiceIndex: number;
  ttsRate: number;
  ttsAutoRead: boolean;

  // Voice input
  isRecording: boolean;

  // Actions
  fetchChannels: () => Promise<void>;
  fetchMessages: (channelId: string, before?: string) => Promise<void>;
  sendMessage: (channelId: string, content: string) => Promise<void>;
  markAsRead: (channelId: string) => Promise<void>;
  setActiveChannel: (channelId: string | null) => void;
  handleWsEvent: (event: { type: string; data: unknown }) => void;

  // TTS actions
  speakMessage: (message: ChatMessage) => void;
  stopSpeaking: () => void;
  setTtsVoiceIndex: (index: number) => void;
  setTtsRate: (rate: number) => void;
  setTtsAutoRead: (auto: boolean) => void;

  // Voice input
  startRecording: () => Promise<Blob | null>;
  stopRecording: () => void;
  transcribeAudio: (blob: Blob) => Promise<string>;
}

let mediaRecorder: MediaRecorder | null = null;
let audioChunks: Blob[] = [];

export const useChatStore = create<ChatState>()((set, get) => ({
  channels: [],
  messages: {},
  activeChannel: null,
  loading: {},
  sending: false,
  error: null,

  // TTS
  ttsEnabled: typeof window !== 'undefined' && 'speechSynthesis' in window,
  ttsSpeaking: false,
  ttsCurrentMessageId: null,
  ...loadTTSPrefs(),

  // Voice
  isRecording: false,

  fetchChannels: async () => {
    set((s) => ({ loading: { ...s.loading, channels: true } }));
    try {
      const data = await api.get<{ channels: ChatChannel[] }>('/chat/channels');
      // Enrich with brand colors from data store
      set({ channels: data.channels, loading: { ...get().loading, channels: false } });
    } catch (err) {
      set({ loading: { ...get().loading, channels: false }, error: (err as Error).message });
    }
  },

  fetchMessages: async (channelId: string, before?: string) => {
    set((s) => ({ loading: { ...s.loading, messages: true } }));
    try {
      const query = before ? { limit: 50, before } : { limit: 50 };
      const data = await api.get<{ messages: ChatMessage[]; count: number }>('/chat/messages/' + channelId, query);
      set((s) => {
        const existing = s.messages[channelId] ?? [];
        const merged = before
          ? [...data.messages, ...existing]
          : data.messages;
        return {
          messages: { ...s.messages, [channelId]: merged },
          loading: { ...s.loading, messages: false },
        };
      });
    } catch (err) {
      set({ loading: { ...get().loading, messages: false }, error: (err as Error).message });
    }
  },

  sendMessage: async (channelId: string, content: string) => {
    set({ sending: true });
    try {
      await api.post('/chat/messages', { channel_id: channelId, content });
      set({ sending: false });
    } catch (err) {
      set({ sending: false, error: (err as Error).message });
    }
  },

  markAsRead: async (channelId: string) => {
    try {
      await api.post(`/chat/read-all/${channelId}`);
      set((s) => ({
        channels: s.channels.map((c) =>
          c.discord_channel_id === channelId ? { ...c, unread_count: 0 } : c
        ),
        messages: {
          ...s.messages,
          [channelId]: (s.messages[channelId] ?? []).map((m) => ({ ...m, is_read: 1 })),
        },
      }));
    } catch {}
  },

  setActiveChannel: (channelId: string | null) => {
    set({ activeChannel: channelId });
    if (channelId) {
      get().fetchMessages(channelId);
      get().markAsRead(channelId);
    }
  },

  handleWsEvent: (event: { type: string; data: unknown }) => {
    if (event.type === 'chat.message') {
      const msg = event.data as ChatMessage;
      set((s) => {
        const existing = s.messages[msg.channel_id] ?? [];
        // Avoid duplicates
        if (existing.some((m) => m.id === msg.id)) return s;
        const newMessages = { ...s.messages, [msg.channel_id]: [...existing, msg] };
        // Update unread count for non-active channels
        const channels = s.channels.map((c) =>
          c.discord_channel_id === msg.channel_id && c.discord_channel_id !== s.activeChannel
            ? { ...c, unread_count: c.unread_count + 1 }
            : c
        );
        return { messages: newMessages, channels };
      });

      // Auto-read TTS
      const state = get();
      if (state.ttsAutoRead && msg.channel_id === state.activeChannel) {
        state.speakMessage(msg);
      }
    }

    if (event.type === 'chat.channel_updated') {
      const data = event.data as { channel_id: string; unread_count: number };
      set((s) => ({
        channels: s.channels.map((c) =>
          c.discord_channel_id === data.channel_id
            ? { ...c, unread_count: data.unread_count }
            : c
        ),
      }));
    }
  },

  // ── TTS ──

  speakMessage: (message: ChatMessage) => {
    if (!window.speechSynthesis) return;

    // Stop any current speech
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(message.content);
    const voices = window.speechSynthesis.getVoices();
    const state = get();

    if (voices[state.ttsVoiceIndex]) {
      utterance.voice = voices[state.ttsVoiceIndex];
    }
    utterance.rate = state.ttsRate;

    utterance.onstart = () => set({ ttsSpeaking: true, ttsCurrentMessageId: message.id });
    utterance.onend = () => set({ ttsSpeaking: false, ttsCurrentMessageId: null });
    utterance.onerror = () => set({ ttsSpeaking: false, ttsCurrentMessageId: null });

    window.speechSynthesis.speak(utterance);
  },

  stopSpeaking: () => {
    window.speechSynthesis.cancel();
    set({ ttsSpeaking: false, ttsCurrentMessageId: null });
  },

  setTtsVoiceIndex: (index: number) => {
    const prefs = { ...loadTTSPrefs(), voiceIndex: index };
    saveTTSPrefs(prefs);
    set({ ttsVoiceIndex: index });
  },

  setTtsRate: (rate: number) => {
    const prefs = { ...loadTTSPrefs(), rate };
    saveTTSPrefs(prefs);
    set({ ttsRate: rate });
  },

  setTtsAutoRead: (auto: boolean) => {
    const prefs = { ...loadTTSPrefs(), autoRead: auto };
    saveTTSPrefs(prefs);
    set({ ttsAutoRead: auto });
  },

  // ── Voice Input ──

  startRecording: async (): Promise<Blob | null> => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunks = [];
      mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });

      return new Promise((resolve) => {
        mediaRecorder!.ondataavailable = (e) => {
          if (e.data.size > 0) audioChunks.push(e.data);
        };

        mediaRecorder!.onstop = () => {
          stream.getTracks().forEach((t) => t.stop());
          const blob = new Blob(audioChunks, { type: 'audio/webm' });
          set({ isRecording: false });
          resolve(blob);
        };

        mediaRecorder!.start();
        set({ isRecording: true });

        // Auto-stop after 60 seconds
        setTimeout(() => {
          if (mediaRecorder?.state === 'recording') {
            mediaRecorder.stop();
          }
        }, 60000);
      });
    } catch (err) {
      set({ isRecording: false });
      console.error('[voice] Recording failed:', err);
      return null;
    }
  },

  stopRecording: () => {
    if (mediaRecorder?.state === 'recording') {
      mediaRecorder.stop();
    }
  },

  transcribeAudio: async (blob: Blob): Promise<string> => {
    const formData = new FormData();
    formData.append('audio', blob, 'recording.webm');

    const token = localStorage.getItem('mc_token');
    const res = await fetch('/api/v1/chat/transcribe', {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });

    if (!res.ok) throw new Error('Transcription failed');
    const data = await res.json();
    return (data.text ?? '').trim();
  },
}));

// ── Subscribe to WebSocket chat events ──

let wsSubscribed = false;

export function subscribeToChatEvents() {
  if (wsSubscribed) return;
  wsSubscribed = true;

  subscribe('chat.message', (event) => {
    useChatStore.getState().handleWsEvent(event);
  });

  subscribe('chat.channel_updated', (event) => {
    useChatStore.getState().handleWsEvent(event);
  });
}