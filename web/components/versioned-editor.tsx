"use client";

import { useState } from "react";

export function VersionedEditor({ initial, version, stale = false }: { initial: string; version: number; stale?: boolean }) {
  const [value, setValue] = useState(initial);
  const [notice, setNotice] = useState("");
  async function save() {
    const response = await fetch("/api/workbench/save", { method: "PUT", headers: { "Content-Type": "application/json", "If-Match": `\"${version}\"` }, body: JSON.stringify({ value }) });
    setNotice(response.status === 409 ? "版本已更新：你的草稿已保留，请比较差异后重试。" : "修订已保存");
  }
  return <section className="editor-card">
    <div className="editor-toolbar"><span>MARKDOWN / 修订 V{version}</span>{stale && <b className="stale">上游已变化</b>}</div>
    <textarea aria-label="成果内容" value={value} onChange={(event) => setValue(event.target.value)} />
    <div className="editor-actions"><span>{notice}</span><button onClick={save}>保存新修订</button></div>
  </section>;
}
