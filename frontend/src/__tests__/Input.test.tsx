import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { Input } from "@/components/ui/Input";

describe("Input", () => {
  it("renders a label bound to the field", () => {
    render(<Input label="Work email" name="email" />);
    expect(screen.getByLabelText("Work email")).toBeInTheDocument();
  });

  it("shows an error message when provided", () => {
    render(<Input label="Password" name="password" error="Password is required" />);
    expect(screen.getByText("Password is required")).toBeInTheDocument();
  });

  it("accepts typed input", async () => {
    render(<Input label="Work email" name="email" />);
    const input = screen.getByLabelText("Work email");
    await userEvent.type(input, "jordan@qcells.com");
    expect(input).toHaveValue("jordan@qcells.com");
  });
});
