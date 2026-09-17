import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { StarRating } from "@/components/ui/StarRating";

describe("StarRating", () => {
  it("renders five stars", () => {
    render(<StarRating value={0} onChange={jest.fn()} />);
    expect(screen.getAllByRole("radio")).toHaveLength(5);
  });

  it("calls onChange with the clicked star's value", async () => {
    const onChange = jest.fn();
    render(<StarRating value={0} onChange={onChange} />);
    await userEvent.click(screen.getByLabelText("4 stars"));
    expect(onChange).toHaveBeenCalledWith(4);
  });

  it("marks the correct star as checked", () => {
    render(<StarRating value={3} onChange={jest.fn()} />);
    expect(screen.getByLabelText("3 stars")).toHaveAttribute("aria-checked", "true");
    expect(screen.getByLabelText("4 stars")).toHaveAttribute("aria-checked", "false");
  });
});
