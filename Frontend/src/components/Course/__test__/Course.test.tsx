import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { Course } from "../Course";

vi.mock("@/components/StarRating/StarRating", () => ({
  StarRating: ({
    rating,
    totalRatings,
  }: {
    rating: number;
    totalRatings?: number;
    showCount?: boolean;
    size?: string;
    readonly?: boolean;
  }) => (
    <div
      data-testid="star-rating"
      role="img"
      aria-label={`Rating: ${rating} out of 5 stars, ${totalRatings ?? 0} ratings`}
    >
      {rating}
    </div>
  ),
}));

const baseCourse = {
  id: 1,
  name: "React Fundamentals",
  description: "Learn React from scratch",
  thumbnail: "https://example.com/thumbnail.jpg",
};

describe("Course", () => {
  it("renders course name, description, and thumbnail", () => {
    render(<Course {...baseCourse} />);

    expect(screen.getByText(baseCourse.name)).toBeInTheDocument();
    expect(screen.getByText(baseCourse.description)).toBeInTheDocument();
    expect(screen.getByAltText(baseCourse.name)).toHaveAttribute(
      "src",
      baseCourse.thumbnail
    );
  });

  it("renders an article element", () => {
    const { container } = render(<Course {...baseCourse} />);

    expect(container.querySelector("article")).toBeInTheDocument();
  });

  it("shows StarRating when average_rating is provided", () => {
    render(
      <Course {...baseCourse} average_rating={4.2} total_ratings={15} />
    );

    expect(screen.getByRole("img", { name: /Rating:/i })).toBeInTheDocument();
  });

  it("does not show rating section when average_rating is undefined", () => {
    render(<Course {...baseCourse} />);

    expect(
      screen.queryByRole("img", { name: /Rating:/i })
    ).not.toBeInTheDocument();
  });
});
