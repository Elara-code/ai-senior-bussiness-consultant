"use client";

import { useEffect, useRef, useState } from "react";

export type AgentEvent = { id: number; type: string; data: Record<string, unknown> };

export function parseSseBlock(block: string): AgentEvent | null {
  let id = 0, type = "message", data = "";
  for (const line of block.split("\n")) {
    if (line.startsWith("id:")) id = Number(line.slice(3).trim());
    if (line.startsWith("event:")) type = line.slice(6).trim();
    if (line.startsWith("data:")) data += line.slice(5).trim();
  }
  if (!id || !data) return null;
  return { id, type, data: JSON.parse(data) as Record<string, unknown> };
}

export function useAgentEvents(url: string) {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [connection, setConnection] = useState<"connecting" | "live" | "reconnecting" | "closed">("connecting");
  const lastId = useRef(0);
  useEffect(() => {
    const controller = new AbortController();
    let retry: ReturnType<typeof setTimeout> | undefined;
    async function connect() {
      try {
        const response = await fetch(url, { headers: lastId.current ? { "Last-Event-ID": String(lastId.current) } : {}, signal: controller.signal });
        if (!response.ok || !response.body) throw new Error("SSE unavailable");
        setConnection("live");
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const blocks = buffer.split("\n\n"); buffer = blocks.pop() ?? "";
          for (const block of blocks) {
            const event = parseSseBlock(block);
            if (event && event.id > lastId.current) { lastId.current = event.id; setEvents((old) => [...old, event]); }
          }
        }
        setConnection("closed");
      } catch (error) {
        if (controller.signal.aborted) return;
        setConnection("reconnecting");
        retry = setTimeout(connect, 1200);
      }
    }
    void connect();
    return () => { controller.abort(); if (retry) clearTimeout(retry); };
  }, [url]);
  return { events, connection, lastEventId: lastId.current };
}
