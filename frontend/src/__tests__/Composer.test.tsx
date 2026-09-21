import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { Composer } from "@/components/chat/Composer";
import type { AttachmentSummary } from "@/lib/types";

const baseProps = {
  onSend: jest.fn(),
  attachments: [] as AttachmentSummary[],
  isUploadingAttachment: false,
  attachmentError: null,
  onAttach: jest.fn(),
  onRemoveAttachment: jest.fn(),
};

describe("Composer", () => {
  it("sends trimmed text and clears the input", async () => {
    const onSend = jest.fn();
    render(<Composer {...baseProps} onSend={onSend} />);
    const input = screen.getByLabelText("Message");
    await userEvent.type(input, "  hello there  ");
    await userEvent.click(screen.getByLabelText("Send message"));
    expect(onSend).toHaveBeenCalledWith("hello there");
    expect(input).toHaveValue("");
  });

  // Attach button / attachment chips / upload indicator.
  it("calls onAttach when a file is selected via the attach button", async () => {
    const onAttach = jest.fn();
    render(<Composer {...baseProps} onAttach={onAttach} />);
    const file = new File(["hello"], "notes.txt", { type: "text/plain" });
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    await userEvent.upload(fileInput, file);
    expect(onAttach).toHaveBeenCalledWith(file);
  });

  it("renders pending attachment chips and removes one on click", async () => {
    const onRemoveAttachment = jest.fn();
    const attachment: AttachmentSummary = {
      id: "att_1",
      conversation_id: "conv_1",
      filename: "site-survey.pdf",
      mime_type: "application/pdf",
      kind: "document",
      size_bytes: 2048,
      has_extracted_text: true,
      uploaded_at: new Date().toISOString(),
    };
    render(<Composer {...baseProps} attachments={[attachment]} onRemoveAttachment={onRemoveAttachment} />);
    expect(screen.getByText("site-survey.pdf")).toBeInTheDocument();
    await userEvent.click(screen.getByLabelText("Remove site-survey.pdf"));
    expect(onRemoveAttachment).toHaveBeenCalledWith("att_1");
  });

  it("shows an uploading indicator while an attachment is in flight", () => {
    render(<Composer {...baseProps} isUploadingAttachment />);
    expect(screen.getByText("Attaching...")).toBeInTheDocument();
  });
});
