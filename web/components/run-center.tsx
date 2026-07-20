"use client";

import { useAgentEvents } from "../hooks/use-agent-events";
import { RunControls } from "./run-controls";
import { RunTimeline } from "./run-timeline";

export function RunCenter({ runId }: { runId: string }) { const { events, connection, lastEventId } = useAgentEvents(`/api/v1/agent-runs/${runId}/events`); return <><div className="run-status"><i className={`pulse ${connection}`} /><div><span>CONNECTION / {connection.toUpperCase()}</span><h2>高级业务顾问正在工作</h2></div><b>LAST EVENT {lastEventId}</b></div><RunTimeline events={events.length ? events : [{id:1,type:"run.started",data:{}},{id:2,type:"plan.created",data:{}},{id:3,type:"step.started",data:{step_id:"solution"}}]} /><RunControls runId={runId} /></>; }
