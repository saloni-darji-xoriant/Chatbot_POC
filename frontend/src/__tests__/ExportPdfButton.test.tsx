import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ExportPdfButton } from "@/components/chat/ExportPdfButton";
import { api } from "@/lib/api";
import { downloadBlob, viewerTimeZone } from "@/lib/download";

jest.mock("@/context/AuthContext", () => ({ useAuth: () => ({ token: "token_u1" }) }));
jest.mock("@/lib/download", () => ({ downloadBlob: jest.fn(), viewerTimeZone: jest.fn() }));

describe("ExportPdfButton", () => {
  afterEach(() => jest.restoreAllMocks());

  it("requests the PDF with the viewer's timezone and downloads it", async () => {
    const blob = new Blob(["%PDF"], { type: "application/pdf" });
    const exportSpy = jest.spyOn(api, "exportConversationPdf").mockResolvedValue({ blob, filename: "chat.pdf" });
    (viewerTimeZone as jest.Mock).mockReturnValue("Asia/Kolkata");

    render(<ExportPdfButton conversationId="conv_1" />);
    await userEvent.click(screen.getByRole("button", { name: "Export chat as PDF" }));

    await waitFor(() => expect(downloadBlob).toHaveBeenCalledWith(blob, "chat.pdf"));
    expect(exportSpy).toHaveBeenCalledWith("token_u1", "conv_1", "Asia/Kolkata");
  });

  it("shows an error message when the export fails", async () => {
    jest.spyOn(api, "exportConversationPdf").mockRejectedValue(new Error("boom"));
    render(<ExportPdfButton conversationId="conv_1" />);
    await userEvent.click(screen.getByRole("button", { name: "Export chat as PDF" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/couldn't export/i);
  });
});
