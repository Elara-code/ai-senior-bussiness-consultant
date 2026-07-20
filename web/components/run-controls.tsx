"use client";

import { useState } from "react";

export function RunControls({ runId, canRetry = false }: { runId: string; canRetry?: boolean }) {
  const [message, setMessage] = useState("");
  async function act(action: "cancel" | "retry") { const response = await fetch(`/api/v1/agent-runs/${runId}:${action}`, { method: "POST" }); setMessage(response.ok ? (action === "cancel" ? "已请求取消" : "已进入重试队列") : "操作失败，请稍后重试"); }
  return <div className="run-controls"><span>{message}</span><button className="secondary" onClick={() => act("cancel")}>取消任务</button>{canRetry && <button className="primary" onClick={() => act("retry")}>从失败步骤重试</button>}</div>;
}
