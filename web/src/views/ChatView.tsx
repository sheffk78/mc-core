import React, { useEffect, useRef, useState } from 'react';
import {
  MessageCircle,
  Send,
  Volume2,
  VolumeX,
  Mic,
  MicOff,
  Square,
  Settings2,
} from 'lucide-react';
import { useChatStore, subscribeToChatEvents, type ChatMessage } from '../stores/chat';
import { useDataStore } from '../stores/data';

// ── Channel List ──

function ChannelList() {
  const channels = useChatStore((s) => s.channels);
  const activeChannel = useChatStore((s) => s.activeChannel);
  const setActiveChannel = useChatStore((s) => s.setActiveChannel);
  const loading = useChatStore((s) => s.loading.channels);
  const brands = useDataStore((s) => s.brands);

  const getBrandColor = (slug: string) => {
    const brand = brands.find((b) => b.slug === slug);
    return brand?.color ?? '#888';
  };

  if (loading && channels.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-4">
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-[var(--mc-border)] border-t-[var(--mc-accent)]" />
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-[var(--mc-border)] px-3 py-2">
        <h2 className="text-[11px] font-semibold uppercase tracking-wider text-[var(--mc-ink-muted)]">
          Channels
        </h2>
      </div>
      <div className="flex-1 overflow-y-auto p-1">
        {channels.map((ch) => {
          const isActive = activeChannel === ch.discord_channel_id;
          const brandColor = getBrandColor(ch.slug);
          return (
            <button
              key={ch.discord_channel_id}
              onClick={() => setActiveChannel(ch.discord_channel_id)}
              className={`mx-1 flex w-[calc(100%-8px)] items-center gap-2 rounded-md px-3 py-2 text-left text-sm transition-colors duration-150 ${
                isActive
                  ? 'bg-[var(--mc-accent)]/10 text-[var(--mc-accent)]'
                  : 'text-[var(--mc-ink-muted)] hover:bg-black/5 hover:text-[var(--mc-ink)]'
              }`}
            >
              <span
                className="h-2 w-2 flex-shrink-0 rounded-full"
                style={{ backgroundColor: brandColor }}
              />
              <span className="flex-1 truncate">{ch.name}</span>
              {ch.unread_count > 0 && (
                <span className="rounded-full bg-[var(--mc-accent)] px-1.5 py-0.5 text-[10px] font-bold text-white">
                  {ch.unread_count}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ── Message Bubble ──

function MessageBubble({ message, onSpeak }: { message: ChatMessage; onSpeak: () => void }) {
  const ttsCurrentMessageId = useChatStore((s) => s.ttsCurrentMessageId);
  const isSpeaking = ttsCurrentMessageId === message.id;
  const isKit = message.is_from_kit === 1;

  const timeStr = new Date(message.created_at).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className={`group flex gap-2.5 ${isKit ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div
        className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full text-[11px] font-bold text-white"
        style={{
          backgroundColor: isKit ? 'var(--mc-accent)' : '#6366f1',
        }}
      >
        {message.discord_author_avatar ? (
          <img
            src={message.discord_author_avatar}
            alt={message.discord_author_name}
            className="h-8 w-8 rounded-full"
          />
        ) : (
          message.discord_author_name?.charAt(0).toUpperCase() ?? "?"
        )}
      </div>

      {/* Message content */}
      <div className={`max-w-[75%] ${isKit ? 'items-end' : 'items-start'} flex flex-col`} role="article" aria-label={`${message.discord_author_name} message`}>
        <div className="flex items-baseline gap-2">
          <span className="text-[11px] font-medium text-[var(--mc-ink)]">
            {message.discord_author_name}
          </span>
          <span className="text-[10px] text-[var(--mc-ink-muted)]">{timeStr}</span>
        </div>
        <div
          className={`mt-0.5 rounded-lg px-3 py-2 text-sm ${
            isKit
              ? 'bg-[var(--mc-accent)]/10 text-[var(--mc-ink)]'
              : 'bg-black/5 text-[var(--mc-ink)]'
          } ${isSpeaking ? 'ring-2 ring-[var(--mc-accent)] ring-offset-1' : ''}`}
          role="text"
          aria-live="polite"
        >
          <p className="m-0">{message.content}</p>
        </div>

        {/* Speak button (appears on hover) */}
        <button
          onClick={onSpeak}
          className="mt-0.5 flex items-center gap-1 text-[10px] text-[var(--mc-ink-muted)] opacity-0 transition-opacity group-hover:opacity-100 hover:text-[var(--mc-accent)]"
        >
          {isSpeaking ? (
            <>
              <VolumeX size={10} />
              Speaking...
            </>
          ) : (
            <>
              <Volume2 size={10} />
              Read aloud
            </>
          )}
        </button>
      </div>
    </div>
  );
}

// ── TTS Controls ──

function TTSControls({ onClose }: { onClose: () => void }) {
  const ttsVoiceIndex = useChatStore((s) => s.ttsVoiceIndex);
  const ttsRate = useChatStore((s) => s.ttsRate);
  const ttsAutoRead = useChatStore((s) => s.ttsAutoRead);
  const setTtsVoiceIndex = useChatStore((s) => s.setTtsVoiceIndex);
  const setTtsRate = useChatStore((s) => s.setTtsRate);
  const setTtsAutoRead = useChatStore((s) => s.setTtsAutoRead);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);

  useEffect(() => {
    const loadVoices = () => {
      const v = window.speechSynthesis.getVoices();
      setVoices(v);
    };
    loadVoices();
    window.speechSynthesis.addEventListener('voiceschanged', loadVoices);
    return () => window.speechSynthesis.removeEventListener('voiceschanged', loadVoices);
  }, []);

  const rates = [0.5, 0.75, 1, 1.25, 1.5, 2];

  return (
    <div className="absolute right-0 top-full z-50 mt-1 w-64 rounded-lg border border-[var(--mc-border)] bg-[var(--mc-surface)] p-3 shadow-lg">
      <div className="mb-3 flex items-center justify-between">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-[var(--mc-ink-muted)]">
          Text-to-Speech
        </span>
        <button onClick={onClose} className="text-[var(--mc-ink-muted)] hover:text-[var(--mc-ink)]">
          ×
        </button>
      </div>

      {/* Voice selection */}
      <label className="mb-2 block text-[11px] text-[var(--mc-ink-muted)]">Voice</label>
      <select
        value={ttsVoiceIndex}
        onChange={(e) => setTtsVoiceIndex(Number(e.target.value))}
        className="mb-3 w-full rounded-md border border-[var(--mc-border)] bg-[var(--mc-bg)] px-2 py-1.5 text-xs text-[var(--mc-ink)]"
      >
        {voices.map((v, i) => (
          <option key={i} value={i}>
            {v.name} ({v.lang})
          </option>
        ))}
      </select>

      {/* Speed */}
      <label className="mb-2 block text-[11px] text-[var(--mc-ink-muted)]">Speed</label>
      <div className="mb-3 flex gap-1">
        {rates.map((r) => (
          <button
            key={r}
            onClick={() => setTtsRate(r)}
            className={`rounded px-2 py-1 text-[11px] ${
              ttsRate === r
                ? 'bg-[var(--mc-accent)] text-white'
                : 'bg-black/5 text-[var(--mc-ink-muted)] hover:bg-black/10'
            }`}
          >
            {r}x
          </button>
        ))}
      </div>

      {/* Auto-read toggle */}
      <label className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={ttsAutoRead}
          onChange={(e) => setTtsAutoRead(e.target.checked)}
          className="rounded border-[var(--mc-border)]"
        />
        <span className="text-xs text-[var(--mc-ink)]">Auto-read new messages</span>
      </label>
    </div>
  );
}

// ── Message Input ──

function MessageInput({ channelId }: { channelId: string }) {
  const [text, setText] = useState('');
  const sending = useChatStore((s) => s.sending);
  const isRecording = useChatStore((s) => s.isRecording);
  const sendMessage = useChatStore((s) => s.sendMessage);
  const startRecording = useChatStore((s) => s.startRecording);
  const stopRecording = useChatStore((s) => s.stopRecording);
  const transcribeAudio = useChatStore((s) => s.transcribeAudio);
  const [recordingError, setRecordingError] = useState<string | null>(null);

  const handleSend = async () => {
    const trimmed = text.trim();
    if (!trimmed || sending) return;
    setText('');
    await sendMessage(channelId, trimmed);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleMicClick = async () => {
    if (isRecording) {
      stopRecording();
      return;
    }

    setRecordingError(null);
    const blob = await startRecording();
    if (!blob) {
      setRecordingError('Microphone access denied');
      return;
    }

    try {
      const transcribed = await transcribeAudio(blob);
      if (!transcribed.trim()) {
        setRecordingError('No speech detected');
        return;
      }
      setText((prev) => prev ? `${prev} ${transcribed}` : transcribed);
    } catch {
      setRecordingError('Transcription failed');
    }
  };

  return (
    <div className="border-t border-[var(--mc-border)] bg-[var(--mc-surface)] p-3">
      {recordingError && (
        <p className="mb-2 text-[11px] text-red-500">{recordingError}</p>
      )}
      <div className="flex items-end gap-2">
        <button
          onClick={handleMicClick}
          className={`flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg transition-colors ${
            isRecording
              ? 'animate-pulse bg-red-500 text-white'
              : 'bg-black/5 text-[var(--mc-ink-muted)] hover:bg-black/10 hover:text-[var(--mc-ink)]'
          }`}
          title={isRecording ? 'Stop recording' : 'Voice input'}
        >
          {isRecording ? <Square size={14} /> : <Mic size={14} />}
        </button>

        <div className="flex-1">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message..."
            rows={1}
            className="w-full resize-none rounded-lg border border-[var(--mc-border)] bg-[var(--mc-bg)] px-3 py-2 text-sm text-[var(--mc-ink)] placeholder:text-[var(--mc-ink-muted)] focus:border-[var(--mc-accent)] focus:outline-none"
            style={{ maxHeight: '120px' }}
            onInput={(e) => {
              const el = e.currentTarget;
              el.style.height = 'auto';
              el.style.height = Math.min(el.scrollHeight, 120) + 'px';
            }}
          />
        </div>

        <button
          onClick={handleSend}
          disabled={!text.trim() || sending}
          className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-[var(--mc-accent)] text-white transition-colors hover:opacity-90 disabled:opacity-50"
        >
          <Send size={14} />
        </button>
      </div>
    </div>
  );
}

// ── Main ChatView ──

export default function ChatView() {
  const channels = useChatStore((s) => s.channels);
  const activeChannel = useChatStore((s) => s.activeChannel);
  const messages = useChatStore((s) => s.messages);
  const ttsSpeaking = useChatStore((s) => s.ttsSpeaking);
  const ttsAutoRead = useChatStore((s) => s.ttsAutoRead);
  const stopSpeaking = useChatStore((s) => s.stopSpeaking);
  const fetchChannels = useChatStore((s) => s.fetchChannels);
  const speakMessage = useChatStore((s) => s.speakMessage);
  const setActiveChannel = useChatStore((s) => s.setActiveChannel);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [showTTSControls, setShowTTSControls] = useState(false);

  // Initial load
  useEffect(() => {
    fetchChannels();
    subscribeToChatEvents();
  }, []);

  // Auto-set active channel when channels load
  useEffect(() => {
    if (!activeChannel && channels.length > 0) {
      setActiveChannel(channels[0].discord_channel_id);
    }
  }, [channels, activeChannel, setActiveChannel]);

  // Auto-scroll on new messages
  useEffect(() => {
    if (activeChannel && messages[activeChannel]) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [activeChannel, messages[activeChannel ?? '']?.length]);

  const activeChannelData = channels.find((c) => c.discord_channel_id === activeChannel);
  const activeMessages = activeChannel ? (messages[activeChannel] ?? []) : [];

  return (
    <div className="flex h-[calc(100vh-120px)]">
      {/* Channel sidebar — fixed, no scroll */}
      <div className="w-[200px] flex-shrink-0 border-r border-[var(--mc-border)] bg-[var(--mc-surface)] overflow-hidden">
        <ChannelList />
      </div>

      {/* Main chat area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {activeChannel && activeChannelData ? (
          <>
            {/* Header — fixed */}
            <div className="flex-shrink-0 flex items-center justify-between border-b border-[var(--mc-border)] px-4 py-2">
              <div className="flex items-center gap-2">
                <span
                  className="h-2.5 w-2.5 rounded-full"
                  style={{ backgroundColor: '#6366f1' }}
                />
                <span className="font-display text-sm font-bold text-[var(--mc-ink)]">
                  {activeChannelData.name}
                </span>
                <span className="text-[11px] text-[var(--mc-ink-muted)]">
                  Discord
                </span>
              </div>

              <div className="flex items-center gap-2">
                {/* TTS toggle */}
                <div className="relative">
                  <button
                    onClick={() => setShowTTSControls(!showTTSControls)}
                    className={`flex items-center gap-1.5 rounded-md px-2 py-1 text-[11px] transition-colors ${
                      ttsAutoRead
                        ? 'bg-[var(--mc-accent)]/10 text-[var(--mc-accent)]'
                        : 'text-[var(--mc-ink-muted)] hover:bg-black/5 hover:text-[var(--mc-ink)]'
                    }`}
                  >
                    <Volume2 size={13} />
                    {ttsAutoRead ? 'Auto-read on' : 'TTS'}
                  </button>
                  {showTTSControls && (
                    <TTSControls onClose={() => setShowTTSControls(false)} />
                  )}
                </div>

                {ttsSpeaking && (
                  <button
                    onClick={stopSpeaking}
                    className="flex items-center gap-1 rounded-md bg-red-500/10 px-2 py-1 text-[11px] text-red-500 hover:bg-red-500/20"
                  >
                    <VolumeX size={13} />
                    Stop
                  </button>
                )}
              </div>
            </div>

            {/* Messages — scrollable area only */}
            <div className="flex-1 overflow-y-auto px-4 py-3">
              <div className="flex flex-col gap-3">
                {activeMessages.map((msg) => (
                  <MessageBubble
                    key={msg.id}
                    message={msg}
                    onSpeak={() => speakMessage(msg)}
                  />
                ))}
                <div ref={messagesEndRef} />
              </div>
              {activeMessages.length === 0 && (
                <div className="flex h-full items-center justify-center text-sm text-[var(--mc-ink-muted)]">
                  No messages yet. Start the conversation!
                </div>
              )}
            </div>

            {/* Input — fixed at bottom */}
            <MessageInput channelId={activeChannel} />
          </>
        ) : (
          <div className="flex h-full items-center justify-center">
            <div className="text-center">
              <MessageCircle size={32} className="mx-auto mb-3 text-[var(--mc-ink-muted)]" />
              <p className="text-sm text-[var(--mc-ink-muted)]">
                Select a channel to start chatting
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}