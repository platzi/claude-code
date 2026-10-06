import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { Course } from "../Course";

describe("Course Component", () => {
  const mockCourse = {
    id: 1,
    name: "React Fundamentals",
    description: "Aprende React desde cero",
    thumbnail: "https://example.com/thumbnail.jpg",
    average_rating: 4.5,
    total_ratings: 12,
  };

  it("renders course information correctly", () => {
    render(<Course {...mockCourse} />);

    expect(screen.getByRole("heading", { name: mockCourse.name })).toBeInTheDocument();
    expect(screen.getByText(mockCourse.description)).toBeInTheDocument();
  });

  it("renders thumbnail with correct alt text", () => {
    render(<Course {...mockCourse} />);

    const thumbnail = screen.getByAltText(mockCourse.name);
    expect(thumbnail).toHaveAttribute("src", mockCourse.thumbnail);
  });

  it("renders the average rating with its count", () => {
    render(<Course {...mockCourse} />);

    expect(
      screen.getByRole("img", { name: "Rating: 4.5 out of 5 stars, 12 ratings" })
    ).toBeInTheDocument();
  });

  it("does not render the rating when average_rating is missing", () => {
    render(<Course {...mockCourse} average_rating={undefined} />);

    expect(screen.queryByRole("img", { name: /Rating:/ })).not.toBeInTheDocument();
  });

  it("renders with correct structure", () => {
    const { container } = render(<Course {...mockCourse} />);

    expect(container.querySelector("article")).toBeInTheDocument();
    expect(container.querySelector("article h2")).toBeInTheDocument();
  });
});
