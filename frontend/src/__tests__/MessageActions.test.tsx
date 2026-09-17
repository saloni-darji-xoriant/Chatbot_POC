import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { MessageActions } from "@/components/chat/MessageActions";

describe("MessageActions", () => {
  it("does not render the Trace button when there is no trace", () => {
    render(
      <MessageActions
        vote={null}
        onVote={jest.fn()}
        hasTrace={false}
        traceActive={false}
        onToggleTrace={jest.fn()}
      />
    );
    expect(screen.queryByLabelText("View developer trace")).not.toBeInTheDocument();
  });

  it("toggles the developer trace panel via the Trace button", async () => {
    const onToggleTrace = jest.fn();
    render(
      <MessageActions
        vote={null}
        onVote={jest.fn()}
        hasTrace
        traceActive={false}
        onToggleTrace={onToggleTrace}
      />
    );
    await userEvent.click(screen.getByLabelText("View developer trace"));
    expect(onToggleTrace).toHaveBeenCalledTimes(1);
  });

  it("shows a reason input after a thumbs-down vote and saves the typed reason", async () => {
    const onVote = jest.fn();
    render(
      <MessageActions vote={null} onVote={onVote} hasTrace={false} traceActive={false} onToggleTrace={jest.fn()} />
    );

    await userEvent.click(screen.getByLabelText("Thumbs down"));
    expect(onVote).toHaveBeenCalledWith("down");

    const reasonInput = screen.getByLabelText("Reason for thumbs down");
    await userEvent.type(reasonInput, "Missed the claim portal URL");
    await userEvent.click(screen.getByRole("button", { name: "Save" }));

    expect(onVote).toHaveBeenLastCalledWith("down", "Missed the claim portal URL");
  });

  it("clears the vote when thumbs-down is clicked again", async () => {
    const onVote = jest.fn();
    render(
      <MessageActions vote="down" onVote={onVote} hasTrace={false} traceActive={false} onToggleTrace={jest.fn()} />
    );
    await userEvent.click(screen.getByLabelText("Thumbs down"));
    expect(onVote).toHaveBeenCalledWith(null);
  });
});
