"use client";
import { useState } from "react";
import { useParams } from "next/navigation";
const content: Record<string, { title: string; kicker: string; desc: string }> = {
  materials: { title: "材料中心", kicker: "SOURCE LIBRARY / 12 ITEMS", desc: "上传、解析并组织项目证据，支持拖拽 PDF、DOCX、Markdown 与 TXT。" },
  runs: { title: "Agent 分析中心", kicker: "AGENT RUN / LIVE", desc: "查看检索、分析、生成和质量检查的业务级进度。" },
  requirements: { title: "需求与场景", kicker: "REQUIREMENTS / BASELINE", desc: "AI 提炼结果由顾问共同确认，所有结论都有事实、推断或待确认标记。" },
  solution: { title: "方案工作室", kicker: "SOLUTION STUDIO / ROADMAP", desc: "按 P0、P1、P2 分阶段生成方案，任何阶段都可与 AI 协同调整。" },
  approvals: { title: "成果与审批", kicker: "REVIEW GATE / 03 PENDING", desc: "审批、退回、问题反馈和版本快照集中在这里完成。" },
  delivery: { title: "交付与知识", kicker: "DELIVERY & KNOWLEDGE", desc: "将已批准方案转成里程碑，并由 AI 筛选脱敏知识资产。" },
};
export default function SectionPage() {
  const { section } = useParams<{ section: string }>();
  const [notice, setNotice] = useState("");
  const page = content[section] ?? content.materials;
  const act = (message: string) => { setNotice(message); window.setTimeout(() => setNotice(""), 2200); };
  return <div className="page project-page">
    <div className="page-title"><div><span className="eyebrow">{page.kicker}</span><h1>{page.title}</h1><p>{page.desc}</p></div><button className="primary" onClick={() => act(section === "materials" ? "样例材料已加入解析队列" : "演示动作已触发")}>{section === "materials" ? "＋ 上传材料" : "与 AI 协同"}</button></div>
    {notice && <div className="offline">{notice}</div>}
    <section className="work-grid"><article className="feature"><span>当前项目 · 日企智能客服升级</span><h2>{section === "solution" ? "分阶段实施路线" : "证据驱动的咨询闭环"}</h2><p>从客户材料到可审批成果，每一步都有负责人和下一动作。</p></article><article><span>项目健康度</span><b className="giant">82</b><small>/ 100</small></article><article><span>待处理</span><h3>{section === "approvals" ? "3 个审批事项" : "2 项信息缺口"}<br />本周完成</h3></article></section>
    <div className="section-head"><h2>{section === "runs" ? "运行时间线" : section === "solution" ? "P0 / P1 / P2" : "工作区操作"}</h2><span>DEMO WORKSPACE</span></div>
    <section className="project-grid">{["P0 · 智能客服知识助手","P1 · 自动化服务报告","P2 · 多渠道智能运营"].map((item, i) => <article className="project-card" key={item}><span className="stage">{item}</span><h2>{section === "runs" ? ["读取并解析材料","混合检索与重排","引用质量检查"][i] : item.split(" · ")[1]}</h2><p>{["已完成 · 12 条事实引用","进行中 · 等待人工确认","待规划 · 依赖前置阶段"][i]}</p><button className="secondary" onClick={() => act("已打开详细信息")}>查看详情 →</button></article>)}</section>
  </div>;
}

