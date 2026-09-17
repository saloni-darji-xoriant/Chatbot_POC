import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { MessageBubble } from "@/components/chat/MessageBubble";
import type { Message } from "@/lib/types";

const baseMessage: Message = {
  id: "msg_1",
  conversation_id: "conv_1",
  sender: "assistant",
  text: "Power-cycle the inverter to clear the fault code.",
  created_at: new Date().toISOString(),
  citations: [{ id: "cit_1", label: "Fault Codes", document: "Inverter-Troubleshooting.md" }],
  quick_replies: ["The fault code came back"],
  process_trace: [],
  attachments: [],
  vote: null,
  is_grounded: true,
};

describe("MessageBubble", () => {
  it("renders assistant text and citation chips", () => {
    render(<MessageBubble message={baseMessage} />);
    expect(screen.getByText(/power-cycle the inverter/i)).toBeInTheDocument();
    expect(screen.getByText("Inverter-Troubleshooting.md")).toBeInTheDocument();
  });

  it("renders quick replies and fires the callback", async () => {
    const onQuickReply = jest.fn();
    render(<MessageBubble message={baseMessage} onQuickReply={onQuickReply} />);
    await userEvent.click(screen.getByText("The fault code came back"));
    expect(onQuickReply).toHaveBeenCalledWith("The fault code came back");
  });

  it("toggles a thumbs-up vote via onVote", async () => {
    const onVote = jest.fn();
    render(<MessageBubble message={baseMessage} onVote={onVote} />);
    await userEvent.click(screen.getByLabelText("Thumbs up"));
    expect(onVote).toHaveBeenCalledWith("up");
  });

  it("renders user messages as a right-aligned bubble without actions", () => {
    const userMessage: Message = { ...baseMessage, sender: "user", text: "My inverter shows E02" };
    render(<MessageBubble message={userMessage} />);
    expect(screen.getByText("My inverter shows E02")).toBeInTheDocument();
    expect(screen.queryByLabelText("Thumbs up")).not.toBeInTheDocument();
  });

  it("shows an attachment chip on a user message that has one", () => {
    const userMessage: Message = {
      ...baseMessage,
      sender: "user",
      text: "See the attached site survey",
      attachments: [
        {
          id: "att_1",
          conversation_id: "conv_1",
          filename: "site-survey.pdf",
          mime_type: "application/pdf",
          kind: "document",
          size_bytes: 12_345,
          has_extracted_text: true,
          uploaded_at: new Date().toISOString(),
        },
      ],
    };
    render(<MessageBubble message={userMessage} />);
    expect(screen.getByText("site-survey.pdf")).toBeInTheDocument();
  });
});
