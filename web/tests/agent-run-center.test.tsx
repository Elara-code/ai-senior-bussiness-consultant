import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { parseSseBlock } from "../hooks/use-agent-events";
import { RunTimeline } from "../components/run-timeline";

describe("agent run center", () => {
  it("parses resumable SSE identifiers", () => { expect(parseSseBlock('id: 7\nevent: step.completed\ndata: {"step_id":"solution"}')).toEqual({id:7,type:"step.completed",data:{step_id:"solution"}}); });
  it("dedicated timeline renders approval gates", () => { render(<RunTimeline events={[{id:4,type:"approval.required",data:{}}]} />); expect(screen.getByText("等待人工审批")).toBeInTheDocument(); });
});
