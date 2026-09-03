"use client";
import { useParams } from "next/navigation";
import { useState } from "react";
import { RunCenter } from "../../../../components/run-center";

export default function RunsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [runId, setRunId] = useState<string>("");
  const [message, setMessage] = useState("尚未启动任务");
  async function start() {
    setMessage("正在创建 Agent 任务…");
    const response = await fetch("/api/v1/projects/" + projectId + "/agent-runs", {
      method: "POST", headers: { "Content-Type": "application/json", "Idempotency-Key": crypto.randomUUID() },
      body: JSON.stringify({ agent: "requirement_analysis", input: { objective: "分析客户材料并提炼需求", document_version_ids: [] }, options: { language: "zh-CN" } }),
    });
    if (!response.ok) { setMessage("服务不可用，当前展示离线时间线"); setRunId("offline"); return; }
    const run = await response.json(); setRunId(run.id); setMessage("任务已启动，正在接收实时事件");
  }
  return <div className="page project-page"><div className="page-title"><div><span className="eyebrow">LIVE AGENT OPERATIONS</span><h1>Agent 运行中心</h1><p>业务事件可恢复，模型私有思维链不会展示。</p></div><button className="primary" onClick={start}>＋ 启动需求分析</button></div><div className="offline">{message}</div>{runId ? <RunCenter runId={runId} /> : <div className="panel" style={{ marginTop: 30 }}><h2>等待启动</h2><p>启动后将实时显示计划、检索、分析和质量检查步骤。</p></div>}</div>;
}

