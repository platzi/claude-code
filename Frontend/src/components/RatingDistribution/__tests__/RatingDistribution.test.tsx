import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { RatingDistribution } from "../RatingDistribution";

describe("RatingDistribution", () => {
  it("renders one row per star from 5 to 1 with count and percentage", () => {
    render(
      <RatingDistribution
        distribution={{ "1": 0, "2": 1, "3": 0, "4": 3, "5": 4 }}
        totalRatings={8}
      />
    );

    const rows = screen.getAllByRole("img");
    expect(rows.map((row) => row.getAttribute("aria-label"))).toEqual([
      "5 estrellas: 4 votos (50%)",
      "4 estrellas: 3 votos (38%)",
      "3 estrellas: 0 votos (0%)",
      "2 estrellas: 1 voto (13%)",
      "1 estrella: 0 votos (0%)",
    ]);
    expect(screen.getByText("8 valoraciones")).toBeInTheDocument();
  });

  it("sets each bar width to its percentage", () => {
    const { container } = render(
      <RatingDistribution
        distribution={{ "1": 1, "2": 0, "3": 0, "4": 0, "5": 3 }}
        totalRatings={4}
      />
    );

    const widths = Array.from(container.querySelectorAll<HTMLElement>(".fill")).map(
      (bar) => bar.style.width
    );
    expect(widths).toEqual(["75%", "0%", "0%", "0%", "25%"]);
  });

  it("handles a total of 0 without dividing by zero", () => {
    const { container } = render(
      <RatingDistribution
        distribution={{ "1": 0, "2": 0, "3": 0, "4": 0, "5": 0 }}
        totalRatings={0}
      />
    );

    expect(container.textContent).not.toMatch(/NaN|Infinity/);
    expect(screen.getByRole("img", { name: "5 estrellas: 0 votos (0%)" })).toBeInTheDocument();
    expect(screen.getByText("0 valoraciones")).toBeInTheDocument();
  });

  it("reads the string keys that come from the JSON response", () => {
    const fromJson = JSON.parse('{"1": 2, "2": 0, "3": 0, "4": 0, "5": 0}');

    render(<RatingDistribution distribution={fromJson} totalRatings={2} />);

    expect(screen.getByRole("img", { name: "1 estrella: 2 votos (100%)" })).toBeInTheDocument();
  });
});
