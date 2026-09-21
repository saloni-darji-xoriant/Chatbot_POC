import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ImageViewer, filenameFromUrl } from "@/components/chat/ImageViewer";
import { downloadBlob } from "@/lib/download";

jest.mock("@/lib/download", () => ({ downloadBlob: jest.fn(), viewerTimeZone: jest.fn() }));

const SRC = "http://localhost:8000/static/kb-images/power-cycle-procedure.png";

const renderViewer = () => render(<ImageViewer src={SRC} alt="Power-cycle order" caption="Power-cycle procedure" />);

describe("ImageViewer", () => {
  afterEach(() => jest.restoreAllMocks());

  it("shows the image inline without a dialog", () => {
    renderViewer();
    expect(screen.getByAltText("Power-cycle order")).toBeInTheDocument();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("opens full-screen when the image is clicked and closes with Escape", async () => {
    renderViewer();
    await userEvent.click(screen.getByRole("button", { name: "Open image: Power-cycle order" }));
    expect(screen.getByRole("dialog", { name: "Power-cycle procedure" })).toBeInTheDocument();

    await userEvent.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("closes with the Close button", async () => {
    renderViewer();
    await userEvent.click(screen.getByRole("button", { name: "Enlarge" }));
    await userEvent.click(screen.getByRole("button", { name: "Close image viewer" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("zooms in and out with the buttons, and resets", async () => {
    renderViewer();
    await userEvent.click(screen.getByRole("button", { name: "Enlarge" }));
    const zoomOut = screen.getByRole("button", { name: "Zoom out" });
    expect(zoomOut).toBeDisabled(); // already at fit
    expect(screen.getByText("100%")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Zoom in" }));
    expect(screen.getByText("150%")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Zoom in" }));
    expect(screen.getByText("200%")).toBeInTheDocument();
    await userEvent.click(zoomOut);
    expect(screen.getByText("150%")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Reset zoom" }));
    expect(screen.getByText("100%")).toBeInTheDocument();
  });

  it("zooms with the keyboard and caps at 400%", async () => {
    renderViewer();
    await userEvent.click(screen.getByRole("button", { name: "Enlarge" }));
    await userEvent.keyboard("+".repeat(10));
    expect(screen.getByText("400%")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Zoom in" })).toBeDisabled();
    await userEvent.keyboard("0");
    expect(screen.getByText("100%")).toBeInTheDocument();
  });

  it("toggles zoom on double-click", async () => {
    renderViewer();
    await userEvent.click(screen.getByRole("button", { name: "Enlarge" }));
    const big = screen.getAllByAltText("Power-cycle order")[1];
    await userEvent.dblClick(big);
    expect(screen.getByText("200%")).toBeInTheDocument();
    await userEvent.dblClick(big);
    expect(screen.getByText("100%")).toBeInTheDocument();
  });

  it("downloads the image as a file named after the URL", async () => {
    const blob = new Blob(["png"], { type: "image/png" });
    global.fetch = jest.fn().mockResolvedValue({ ok: true, blob: () => Promise.resolve(blob) }) as unknown as typeof fetch;
    renderViewer();

    await userEvent.click(screen.getByRole("button", { name: "Download image: Power-cycle order" }));
    await waitFor(() => expect(downloadBlob).toHaveBeenCalledWith(blob, "power-cycle-procedure.png"));
    expect(global.fetch).toHaveBeenCalledWith(SRC, { cache: "reload" });
  });

  it("falls back to opening the image in a new tab if the download fails", async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error("offline")) as unknown as typeof fetch;
    const open = jest.spyOn(window, "open").mockImplementation(() => null);
    renderViewer();

    await userEvent.click(screen.getByRole("button", { name: "Download image: Power-cycle order" }));
    await waitFor(() => expect(open).toHaveBeenCalledWith(SRC, "_blank", "noopener,noreferrer"));
  });

  it("offers a new-tab link inside the viewer", async () => {
    renderViewer();
    await userEvent.click(screen.getByRole("button", { name: "Enlarge" }));
    const link = screen.getByRole("link", { name: "Open image in a new tab" });
    expect(link).toHaveAttribute("href", SRC);
    expect(link).toHaveAttribute("target", "_blank");
  });
});

describe("filenameFromUrl", () => {
  it("takes the last path segment and ignores the query string", () => {
    expect(filenameFromUrl("http://x/static/kb-images/a-b.png?v=2")).toBe("a-b.png");
  });
  it("falls back when there is no filename", () => {
    expect(filenameFromUrl("http://x/", "image.png")).toBe("image.png");
  });
});
