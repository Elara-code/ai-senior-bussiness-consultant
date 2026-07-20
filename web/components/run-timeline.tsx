import type { AgentEvent } from "../hooks/use-agent-events";

const labels: Record<string, string> = { "run.started": "任务已启动", "plan.created": "执行计划已建立", "step.started": "专业步骤进行中", "step.completed": "步骤已完成", "approval.required": "等待人工审批", "run.resumed": "已从检查点恢复", "run.completed": "任务已完成", "run.failed": "任务执行失败" };

export function RunTimeline({ events }: { events: AgentEvent[] }) { return <ol className="run-timeline">{events.map((event) => <li key={event.id} className={event.type.includes("failed") ? "failed" : ""}><span>{String(event.id).padStart(2,"0")}</span><div><b>{labels[event.type] ?? event.type}</b><small>{event.data.step_id ? `步骤：${event.data.step_id}` : `事件 ${event.type}`}</small></div></li>)}</ol>; }
