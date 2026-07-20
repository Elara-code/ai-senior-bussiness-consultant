import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ApprovalPanel } from "../components/approval-panel";
import { CitationDrawer } from "../components/citation-drawer";
import { VersionedEditor } from "../components/versioned-editor";

afterEach(() => vi.restoreAllMocks());
describe("governed workbench", () => {
  it("opens evidence without exposing it by default", () => { render(<CitationDrawer citation={{id:"CIT-1",document:"访谈",page:2,quote:"原文"}} />); expect(screen.queryByRole("dialog")).not.toBeInTheDocument(); fireEvent.click(screen.getByText("CIT-1")); expect(screen.getByRole("dialog")).toHaveTextContent("原文"); });
  it("keeps the draft when optimistic locking conflicts", async () => { vi.stubGlobal("fetch", vi.fn().mockResolvedValue({status:409})); render(<VersionedEditor initial="草稿" version={1} />); fireEvent.change(screen.getByLabelText("成果内容"), {target:{value:"我的修改"}}); fireEvent.click(screen.getByText("保存新修订")); expect(await screen.findByText(/草稿已保留/)).toBeInTheDocument(); expect(screen.getByDisplayValue("我的修改")).toBeInTheDocument(); });
  it("requires confirmation before approval", () => { render(<ApprovalPanel />); fireEvent.click(screen.getByText("批准此快照")); expect(screen.getByText(/确认批准/)).toBeInTheDocument(); expect(screen.queryByText(/操作已留痕/)).not.toBeInTheDocument(); });
});
