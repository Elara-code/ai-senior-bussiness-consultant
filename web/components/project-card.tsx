import Link from "next/link";
import type { Project } from "../lib/api";

const labels: Record<Project["stage"], string> = {
  discovery: "需求探索", requirements: "需求确认", solution: "方案设计",
  proposal: "提案评审", delivery: "交付实施", closed: "已结项",
};

export function ProjectCard({ project, index }: { project: Project; index: number }) {
  return (
    <Link className="project-card" href={`/projects/${project.id}`} style={{ "--delay": `${index * 70}ms` } as React.CSSProperties}>
      <span className="folio">0{index + 1}</span>
      <div><span className={`stage stage-${project.stage}`}>{labels[project.stage]}</span>
        <h2>{project.name}</h2><p>{project.description || "等待补充客户背景与项目目标"}</p>
      </div>
      <div className="card-foot"><span>最近更新</span><b>{new Date(project.updated_at).toLocaleDateString("zh-CN")}</b><i>进入项目 →</i></div>
    </Link>
  );
}
