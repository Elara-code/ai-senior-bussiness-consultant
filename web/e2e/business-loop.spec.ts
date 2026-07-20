import { expect, test } from "@playwright/test";

test("consulting workbench exposes the complete phase-two loop", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "项目作战室" })).toBeVisible();
  const projectLink = page.getByRole("link", { name: /进入项目|打开项目/ }).first();
  await expect(projectLink).toBeVisible();
  await projectLink.click();
  await expect(page.getByText(/材料|需求|方案/).first()).toBeVisible();
  await page.getByRole("link", { name: "Agent 运行" }).click();
  await expect(page.getByRole("heading", { name: /运行中心/ })).toBeVisible();
});
