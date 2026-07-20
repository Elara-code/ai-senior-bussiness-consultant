import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ProjectCard } from "../components/project-card";

describe("project dashboard", () => {
  it("renders an accessible project link and stage", () => {
    render(<ProjectCard index={0} project={{ id: "p1", name: "客服升级", description: "试点", stage: "solution", updated_at: "2026-07-20" }} />);
    expect(screen.getByRole("link", { name: /客服升级/ })).toHaveAttribute("href", "/projects/p1");
    expect(screen.getByText("方案设计")).toBeInTheDocument();
  });
});
