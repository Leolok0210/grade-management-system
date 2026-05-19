import { useState, useCallback, useRef, useEffect } from "react";
import { chatApi } from "../api/client";
import type { ChatMessage, DataCard, ConversationItem } from "../types";

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeDataCard, setActiveDataCard] = useState<DataCard | null>(null);
  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const conversationIdRef = useRef<number | null>(null);
  const streamingMsgIdRef = useRef<string | null>(null);

  // 逐字顯示效果
  useEffect(() => {
    if (!streamingMsgIdRef.current) return;
    const msgId = streamingMsgIdRef.current;
    const interval = setInterval(() => {
      setMessages((prev) => {
        const msg = prev.find((m) => m.id === msgId);
        if (!msg || !msg._fullContent) return prev;
        const nextLen = (msg._displayLen || 0) + 2;
        if (nextLen >= msg._fullContent.length) {
          streamingMsgIdRef.current = null;
          return prev.map((m) =>
            m.id === msgId ? { ...m, content: msg._fullContent, _fullContent: undefined, _displayLen: undefined } : m
          );
        }
        return prev.map((m) =>
          m.id === msgId ? { ...m, content: msg._fullContent.slice(0, nextLen), _displayLen: nextLen } : m
        );
      });
    }, 16);
    return () => clearInterval(interval);
  }, [streamingMsgIdRef.current]);

  const loadConversations = useCallback(async () => {
    try {
      const { data } = await chatApi.getConversations();
      setConversations(data);
    } catch {}
  }, []);

  const loadConversation = useCallback(async (convId: number) => {
    try {
      const { data } = await chatApi.getConversation(convId);
      conversationIdRef.current = convId;
      const loaded: ChatMessage[] = (data.messages || []).map((m, i) => ({
        id: `${convId}-${i}`,
        role: m.role as "user" | "assistant",
        content: m.content,
        timestamp: "",
      }));
      setMessages(loaded);
      setActiveDataCard(null);
      streamingMsgIdRef.current = null;
    } catch {}
  }, []);

  const sendMessage = useCallback(async (content: string) => {
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const { data } = await chatApi.sendMessage({
        conversation_id: conversationIdRef.current || undefined,
        message: content,
      });

      conversationIdRef.current = data.conversation_id;

      const assistantMsgId = crypto.randomUUID();
      const assistantMsg: ChatMessage = {
        id: assistantMsgId,
        role: "assistant",
        content: "",
        timestamp: new Date().toISOString(),
        dataCard: data.data_card || undefined,
        _fullContent: data.reply,
        _displayLen: 0,
      };
      streamingMsgIdRef.current = assistantMsgId;
      setMessages((prev) => [...prev, assistantMsg]);

      if (data.data_card) {
        setActiveDataCard(data.data_card);
      }

      // 刷新對話列表
      loadConversations();
    } catch (err) {
      const errorMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "抱歉，發生錯誤，請稍後再試。",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  }, [loadConversations]);

  const clearChat = useCallback(() => {
    setMessages([]);
    conversationIdRef.current = null;
    setActiveDataCard(null);
    streamingMsgIdRef.current = null;
  }, []);

  return {
    messages,
    setMessages,
    loading,
    activeDataCard,
    conversations,
    sendMessage,
    clearChat,
    setActiveDataCard,
    loadConversations,
    loadConversation,
  };
}