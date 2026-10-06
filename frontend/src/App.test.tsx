import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import { getHealth } from "./services/api";

vi.mock("./services/api", () => ({
  getHealth: vi.fn(),
}));

const mockHealth = vi.mocked(getHealth);

describe("application shell", () => {
  beforeEach(() => {
    mockHealth.mockReset();
    mockHealth.mockResolvedValue({
      status: "ok",
      service: "visual-shopping-assistant-api",
      version: "0.1.0",
    });
  });

  it("shows the home layout and API connection state", async () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: /find the pieces/i })).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: /main navigation/i })).toBeInTheDocument();
    await waitFor(() => expect(screen.getAllByRole("status")[0]).toHaveTextContent("API connected"));
  });

  it("navigates to the status route and displays health details", async () => {
    render(<App />);
    fireEvent.click(screen.getByRole("link", { name: "Status" }));
    expect(await screen.findByRole("heading", { name: "Application foundation" })).toBeInTheDocument();
    expect(await screen.findByText("visual-shopping-assistant-api")).toBeInTheDocument();
    expect(screen.getByText("0.1.0")).toBeInTheDocument();
  });

  it("shows a useful status when the backend is unavailable", async () => {
    mockHealth.mockRejectedValue(new Error("Backend request failed (503)"));
    render(<App />);
    await waitFor(() => expect(screen.getAllByRole("status")[0]).toHaveTextContent("API unavailable"));
    expect(screen.getByText("Backend request failed (503)")).toBeInTheDocument();
  });
});

