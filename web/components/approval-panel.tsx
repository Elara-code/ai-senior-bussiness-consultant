"use client";

import { useState } from "react";

export function ApprovalPanel({ status = "awaiting_approval" }: { status?: string }) {
  const [action, setAction] = useState<"approve" | "reject" | null>(null);
  const [done, setDone] = useState("");
  return <section className="approval-card"><span className="eyebrow">GOVERNANCE GATE</span><h3>对客方案审批</h3><p>快照版本 V3 · 状态：{status === "awaiting_approval" ? "等待审批" : status}</p>
    {!action && <div className="approval-actions"><button className="secondary" onClick={() => setAction("reject")}>退回修改</button><button className="primary" onClick={() => setAction("approve")}>批准此快照</button></div>}
    {action && !done && <div className="confirm"><b>确认{action === "approve" ? "批准" : "退回"}不可变快照？</b><textarea aria-label="审批意见" placeholder="填写审批意见" /><button onClick={() => setAction(null)}>取消</button><button className="primary" onClick={() => setDone(action === "approve" ? "已批准" : "已退回")}>确认</button></div>}
    {done && <strong className="decision">{done} · 操作已留痕</strong>}
  </section>;
}
