import { useState, useCallback, useRef } from "react";
import { chatApi } from "../api/client";
import type { ChatMessage, DataCard } from "../types";

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeDataCard, setActiveDataCard] = useState<DataCard | null>(null);
  const conversationIdRef = useRef<string | null>(null);

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

      const assistantMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: data.reply,
        timestamp: new Date().toISOString(),
        dataCard: data.data_card || undefined,
      };
      setMessages((prev) => [...prev, assistantMsg]);

      if (data.data_card) {
        setActiveDataCard(data.data_card);
      }
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
  }, []);

  const clearChat = useCallback(() => {
    setMessages([]);
    conversationIdRef.current = null;
    setActiveDataCard(null);
  }, []);

  return { messages, loading, activeDataCard, sendMessage, clearChat, setActiveDataCard };
}