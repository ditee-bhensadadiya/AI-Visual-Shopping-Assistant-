import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import { detectUpload, getHealth, uploadImage } from "./services/api";

vi.mock("./services/api", () => ({
  getHealth: vi.fn(),
  uploadImage: vi.fn(),
  detectUpload: vi.fn(),
}));

const mockHealth = vi.mocked(getHealth);
const mockUpload = vi.mocked(uploadImage);
const mockDetect = vi.mocked(detectUpload);

describe("application shell", () => {
  beforeEach(() => {
    mockHealth.mockReset();
    mockUpload.mockReset();
    mockDetect.mockReset();
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

  it("uploads an image and shows the private preview and processing status", async () => {
    mockUpload.mockResolvedValue({
      id: "upload-123",
      file_type: "image/png",
      file_size: 68,
      processing_status: "uploaded",
      image_url: "https://example.test/signed-image.png",
      created_at: "2026-10-07T00:00:00Z",
    });
    render(<App />);
    fireEvent.click(screen.getByRole("link", { name: "Upload" }));
    const file = new File([new Uint8Array([1, 2, 3])], "look.png", { type: "image/png" });
    fireEvent.change(screen.getByLabelText("Choose an image"), { target: { files: [file] } });
    fireEvent.click(screen.getByRole("button", { name: "Upload image" }));
    expect(await screen.findByText("Image uploaded · Status: uploaded")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Uploaded image" })).toHaveAttribute("src", "https://example.test/signed-image.png");
    expect(mockUpload).toHaveBeenCalledWith(file);
  });

  it("rejects unsupported image types before sending a request", async () => {
    render(<App />);
    fireEvent.click(screen.getByRole("link", { name: "Upload" }));
    const file = new File(["text"], "notes.txt", { type: "text/plain" });
    fireEvent.change(screen.getByLabelText("Choose an image"), { target: { files: [file] } });
    expect(await screen.findByRole("alert")).toHaveTextContent("Choose a JPEG, PNG, or WebP image");
    expect(mockUpload).not.toHaveBeenCalled();
  });

  it("runs detection and displays bounding boxes and stored crops", async () => {
    mockUpload.mockResolvedValue({
      id: "upload-123", file_type: "image/png", file_size: 68,
      processing_status: "uploaded", image_url: "https://example.test/image.png",
      created_at: "2026-10-07T00:00:00Z",
    });
    mockDetect.mockResolvedValue({
      upload_id: "upload-123", processing_status: "completed",
      image_width: 100, image_height: 100,
      detections: [{
        id: "detection-1", class_name: "handbag", confidence: 0.91,
        box: { x1: 10, y1: 12, x2: 80, y2: 90 },
        crop_url: "https://example.test/crop.jpg",
      }],
    });
    render(<App />);
    fireEvent.click(screen.getByRole("link", { name: "Upload" }));
    const file = new File([new Uint8Array([1, 2, 3])], "look.png", { type: "image/png" });
    fireEvent.change(screen.getByLabelText("Choose an image"), { target: { files: [file] } });
    fireEvent.click(screen.getByRole("button", { name: "Upload image" }));
    await screen.findByText("Upload ID: upload-123");
    fireEvent.click(screen.getByRole("button", { name: "Detect products" }));
    expect(await screen.findByRole("img", { name: "Detected object bounding boxes" })).toBeInTheDocument();
    expect(screen.getByText("Image uploaded · Status: completed")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "handbag crop" })).toHaveAttribute("src", "https://example.test/crop.jpg");
    expect(screen.getByRole("button", { name: "Detection complete · 1 found" })).toBeDisabled();
    expect(mockDetect).toHaveBeenCalledWith("upload-123");
  });
});

