import { useState, useCallback, useRef } from "react";
import { chatApi } from "../api/client";
import type { ChatMessage, DataCard, ConversationItem } from "../types";

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeDataCard, setActiveDataCard] = useState<DataCard | null>(null);
  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const conversationIdRef = useRef<number | null>(null);

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

    const assistantMsgId = crypto.randomUUID();
    const assistantMsg: ChatMessage = {
      id: assistantMsgId,
      role: "assistant",
      content: "",
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, assistantMsg]);

    try {
      const token = localStorage.getItem("access_token");
      const baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

      const response = await fetch(`${baseUrl}/chat/message/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
          "ngrok-skip-browser-warning": "true",
        },
        body: JSON.stringify({
          conversation_id: conversationIdRef.current || undefined,
          message: content,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const jsonStr = line.slice(6);
          if (!jsonStr.trim()) continue;

          try {
            const event = JSON.parse(jsonStr);
            const eventType = event.type;

            if (eventType === "status") {
              // 更新狀態提示
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsgId
                    ? { ...m, _status: event.message }
                    : m
                )
              );
            } else if (eventType === "data_card") {
              // 推送表格/圖表數據
              const card = event.card as DataCard;
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsgId
                    ? { ...m, dataCard: card, dataCards: [...(m.dataCards || []), card] }
                    : m
                )
              );
              setActiveDataCard(card);
            } else if (eventType === "content") {
              // 串流文字
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsgId
                    ? { ...m, content: m.content + (event.text || ""), _status: undefined }
                    : m
                )
              );
            } else if (eventType === "done") {
              // 完成
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsgId ? { ...m, _status: undefined } : m
                )
              );
            }
          } catch {
            // 忽略解析錯誤
          }
        }
      }

      // 刷新對話列表，取得 conversation_id
      const { data: convs } = await chatApi.getConversations();
      setConversations(convs);
      if (convs.length > 0) {
        conversationIdRef.current = convs[0].id;
      }
    } catch (err) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMsgId
            ? { ...m, content: "抱歉，發生錯誤，請稍後再試。", _status: undefined }
            : m
        )
      );
    } finally {
      setLoading(false);
    }
  }, []);

  const clearChat = useCallback(() => {
    setMessages([]);
    conversationIdRef.current = null;
    setActiveDataCard(null);
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
