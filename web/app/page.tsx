"use client";
import { useEffect, useState } from "react";
import { ProjectCard } from "../components/project-card";
import { createProject, listProjects, type Project } from "../lib/api";

const demo: Project[] = [
  { id: "demo", name: "日企智能客服升级", description: "从坐席访谈到试点方案的完整咨询闭环", stage: "solution", updated_at: new Date().toISOString() },
];

export default function Home() {
  const [created, setCreated] = useState(false);
  const [notice, setNotice] = useState("");
  const [projects, setProjects] = useState<Project[]>(demo);
  const [offline, setOffline] = useState(false);
  useEffect(() => { listProjects().then(setProjects).catch(() => setOffline(true)); }, []);
  const create = async () => { try { const project = await createProject({ name: demo[0].name, description: demo[0].description }); setProjects((items) => [project, ...items]); setCreated(true); setNotice("项目已创建，正在进入项目概览"); window.setTimeout(() => { window.location.href = "/projects/" + project.id; }, 700); } catch { setNotice("服务暂不可用，已切换到演示项目"); setCreated(true); } };
  return <div className="page dashboard">
    <header className="masthead"><div><span className="eyebrow">CONSULTING OPERATIONS / 2026</span><h1>项目作战室</h1><p>从客户材料到可审批成果，让每一步专业判断都有证据、有版本、有负责人。</p></div>
      <button className="primary" onClick={create}>＋ 新建客户项目</button></header>
    {notice && <div className="offline">{notice}</div>}
    {offline && <div className="offline">预览模式 · 配置服务端开发身份后将显示真实项目</div>}
    <section className="metrics" aria-label="项目指标"><article><b>{projects.length}</b><span>活跃项目</span></article><article><b>03</b><span>待审批成果</span></article><article><b>96%</b><span>事实引用覆盖</span></article></section>
    <div className="section-head"><h2>进行中的项目</h2><span>{projects.length} PROJECTS</span></div>
    <section className="project-grid">{projects.map((project, index) => <ProjectCard key={project.id} project={project} index={index} />)}{created && <ProjectCard project={demo[0]} index={1} />}</section>
  </div>;
}

