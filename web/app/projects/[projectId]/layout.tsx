import Link from "next/link";
import type { ReactNode } from "react";

const tabs = [["", "项目概览"], ["materials", "材料中心"], ["requirements", "需求与场景"], ["solution", "方案工作室"], ["runs", "Agent 运行"], ["approvals", "成果与审批"], ["delivery", "交付与知识"]];

export default async function ProjectLayout({ children, params }: { children: ReactNode; params: Promise<{ projectId: string }> }) {
  const { projectId } = await params;
  return <div className="project-shell"><header className="project-top"><Link href="/">← 所有项目</Link><div><span>PROJECT / {projectId.slice(0, 8).toUpperCase()}</span><b>日企智能客服升级</b></div><i>方案设计中</i></header>
    <nav className="project-tabs" aria-label="项目导航">{tabs.map(([path, label]) => <Link key={label} href={`/projects/${projectId}/${path}`}>{label}</Link>)}</nav>{children}</div>;
}
