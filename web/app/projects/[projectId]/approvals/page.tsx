"use client";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ApprovalPanel } from "../../../../components/approval-panel";
export default function ApprovalsPage() {
  const { projectId } = useParams<{ projectId: string }>(); const [items, setItems] = useState<any[]>([]); const [notice, setNotice] = useState("");
  useEffect(() => { fetch("/api/v1/projects/" + projectId + "/approvals").then((r) => r.ok ? r.json() : []).then(setItems).catch(() => setItems([])); }, [projectId]);
  async function decide(id: string, decision: "approved" | "rejected") { const r = await fetch("/api/v1/projects/" + projectId + "/approvals/" + id + "/decision", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ decision, expected_target_version: 1, comment: decision === "rejected" ? "请补充风险与验收边界" : "确认通过" }) }); setNotice(r.ok ? (decision === "approved" ? "审批已通过" : "已退回并记录问题反馈") : "审批失败，请刷新后重试"); }
  return <div className="page project-page"><div className="page-title"><div><span className="eyebrow">APPROVAL LEDGER</span><h1>成果与审批</h1><p>批准、退回和问题反馈都会形成不可变记录。</p></div></div>{notice && <div className="offline">{notice}</div>}<ApprovalPanel /><section className="history"><h2>审批记录</h2>{items.length ? items.map((item) => <p key={item.id}><b>{item.target_kind} V{item.target_version}</b><span>{item.status}<button className="secondary" onClick={() => decide(item.id, "rejected")}>退回</button> <button className="primary" onClick={() => decide(item.id, "approved")}>批准</button></span></p>) : <p><b>需求基线 V2</b><span>演示审批记录 · 可在后端创建后实时显示</span></p>}</section></div>;
}

