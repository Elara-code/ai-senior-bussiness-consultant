"use client";
import { useParams } from "next/navigation";
import { useState } from "react";
const seed = ["客户访谈纪要.docx", "客服业务现状.pdf", "系统接口清单.xlsx"];
export default function MaterialsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [files, setFiles] = useState(seed); const [notice, setNotice] = useState("");
  async function upload(file?: File) { if (!file) return; const body = new FormData(); body.append("file", file); const response = await fetch("/api/v1/projects/" + projectId + "/documents", { method: "POST", body }); if (response.ok) { setFiles((items) => [file.name, ...items]); setNotice("材料已上传，正在解析与索引"); } else setNotice("上传失败，请检查文件格式或重试"); }
  return <div className="page project-page"><div className="page-title"><div><span className="eyebrow">SOURCE LIBRARY</span><h1>材料中心</h1><p>支持 PDF、DOCX、Markdown、TXT；上传后自动解析并建立引用。</p></div><label className="primary">＋ 导入材料<input hidden type="file" accept=".pdf,.docx,.md,.txt" onChange={(e) => upload(e.target.files?.[0])} /></label></div>{notice && <div className="offline">{notice}</div>}<section className="table-card"><div className="table-row head"><span>材料</span><span>处理状态</span><span>版本</span><span>引用</span></div>{files.map((name,index)=><div className="table-row" key={name + index}><b>{name}</b><span className="ok">● 已完成索引</span><span>V{index+1}</span><span>{Math.max(0,12-index*3)} 处</span></div>)}</section><div style={{ marginTop: 24 }}><button className="primary" onClick={() => setNotice("需求分析 Agent 已排队，可前往 Agent 分析中心查看")}>开始 AI 需求分析</button></div></div>;
}

