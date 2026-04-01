import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { Course } from "../Course";

describe("Course Component", () => {
  const mockCourse = {
    id: 1,
    name: "React Fundamentals",
    description: "Learn React from scratch",
    thumbnail: "https://example.com/thumbnail.jpg",
  };

  it("renders course information correctly", () => {
    render(<Course {...mockCourse} />);

    expect(screen.getByText(mockCourse.name)).toBeDefined();
    expect(screen.getByText(mockCourse.description)).toBeDefined();
  });

  it("renders thumbnail with correct alt text", () => {
    render(<Course {...mockCourse} />);

    const thumbnail = screen.getByRole("img");
    expect(thumbnail).toHaveAttribute("src", mockCourse.thumbnail);
    expect(thumbnail).toHaveAttribute("alt", mockCourse.name);
  });

  it("renders with correct structure", () => {
    const { container } = render(<Course {...mockCourse} />);

    expect(container.querySelector("article")).toBeDefined();
    expect(container.querySelector("div > img")).toBeDefined();
    expect(container.querySelector("div > h2")).toBeDefined();
    expect(container.querySelector("div > p")).toBeDefined();
  });

  it("renders StarRating when average_rating is provided", () => {
    render(<Course {...mockCourse} average_rating={4.2} total_ratings={10} />);

    const ratingContainer = screen.getByRole("img", { name: /rating/i });
    expect(ratingContainer).toBeInTheDocument();
  });

  it("does not render StarRating when average_rating is not provided", () => {
    render(<Course {...mockCourse} />);

    const ratingContainer = screen.queryByRole("img", { name: /rating/i });
    expect(ratingContainer).not.toBeInTheDocument();
  });
});
