"use client";

import { useState } from "react";

export function CitationDrawer({ citation }: { citation: { id: string; document: string; page: number; quote: string } }) {
  const [open, setOpen] = useState(false);
  return <><button className="citation-chip" onClick={() => setOpen(true)}>{citation.id}</button>
    {open && <aside className="drawer" role="dialog" aria-label="引用证据"><button className="drawer-close" onClick={() => setOpen(false)}>关闭</button><span>TRACEABLE EVIDENCE</span><h3>{citation.document}</h3><small>第 {citation.page} 页</small><blockquote>{citation.quote}</blockquote><button className="secondary">查看原始材料</button></aside>}</>;
}
