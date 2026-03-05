import React from "react";
import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import PreferenceForm from "./components/PreferenceForm.jsx";

describe("PreferenceForm", () => {
  it("submits user preferences to the callback", () => {
    const handleSubmit = vi.fn();
    render(<PreferenceForm onSubmit={handleSubmit} />);

    const locationInput = screen.getByLabelText(/Location \(city\)/i);
    const cuisinesInput = screen.getByLabelText(/Cuisines \(comma separated\)/i);
    const button = screen.getByRole("button", { name: /get recommendations/i });

    fireEvent.change(locationInput, { target: { value: "Mumbai" } });
    fireEvent.change(cuisinesInput, { target: { value: "Italian" } });
    fireEvent.click(button);

    expect(handleSubmit).toHaveBeenCalledTimes(1);
    const payload = handleSubmit.mock.calls[0][0];
    expect(payload.location).toBe("Mumbai");
    expect(payload.cuisines).toEqual(["Italian"]);
  });
});

