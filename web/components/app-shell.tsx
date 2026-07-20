import Link from "next/link";
import type { ReactNode } from "react";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="shell">
      <aside className="rail">
        <Link className="brand" href="/" aria-label="渡河顾问台首页">
          <span className="brand-mark">渡</span>
          <span>渡河<br /><small>AI CONSULTING</small></span>
        </Link>
        <nav aria-label="全局导航">
          <Link className="nav-active" href="/">项目作战室</Link>
          <span>知识资产</span><span>评测中心</span><span>平台设置</span>
        </nav>
        <div className="rail-note"><b>证据优先</b><br />每个结论都有来处，每次批准都有记录。</div>
      </aside>
      <main>{children}</main>
    </div>
  );
}
