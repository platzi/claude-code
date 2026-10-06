import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { CourseDetailComponent } from "../CourseDetail";
import { CourseDetail } from "@/types";

const mockCourse: CourseDetail = {
  id: 1,
  name: "Curso de React",
  description: "Aprende React desde cero",
  thumbnail: "https://example.com/react.jpg",
  slug: "curso-de-react",
  teacher_id: [1, 2],
  teachers: [
    { id: 1, name: "Juan Pérez" },
    { id: 2, name: "María García" },
  ],
  classes: [
    { id: 10, name: "Introducción a React", description: "JSX y componentes", slug: "intro" },
    { id: 11, name: "Estado y Eventos", description: "useState", slug: "estado" },
  ],
  average_rating: 4.5,
  total_ratings: 2,
  rating_distribution: { "1": 0, "2": 0, "3": 0, "4": 1, "5": 1 },
};

describe("CourseDetailComponent", () => {
  it("renders the course name as heading and thumbnail alt", () => {
    render(<CourseDetailComponent course={mockCourse} />);

    expect(screen.getByRole("heading", { level: 1, name: "Curso de React" })).toBeInTheDocument();
    expect(screen.getByAltText("Curso de React")).toBeInTheDocument();
  });

  it("renders the number of classes and a link per class", () => {
    render(<CourseDetailComponent course={mockCourse} />);

    expect(screen.getByText("2 clases")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Introducción a React/ })).toHaveAttribute(
      "href",
      "/classes/10"
    );
    expect(screen.getByRole("link", { name: /Estado y Eventos/ })).toHaveAttribute(
      "href",
      "/classes/11"
    );
  });

  it("renders teachers only when they are provided", () => {
    const { unmount } = render(<CourseDetailComponent course={mockCourse} />);
    expect(screen.getByText("Por Juan Pérez, María García")).toBeInTheDocument();
    unmount();

    render(<CourseDetailComponent course={{ ...mockCourse, teachers: undefined }} />);
    expect(screen.queryByText(/^Por /)).not.toBeInTheDocument();
  });

  it("never renders undefined or NaN", () => {
    const { container } = render(<CourseDetailComponent course={mockCourse} />);

    expect(container.textContent).not.toMatch(/undefined|NaN/);
  });

  describe("ratings section", () => {
    it("shows the average, the count and the distribution", () => {
      render(<CourseDetailComponent course={mockCourse} />);

      expect(screen.getByRole("heading", { level: 2, name: "Valoraciones" })).toBeInTheDocument();
      expect(
        screen.getByRole("img", { name: "Rating: 4.5 out of 5 stars, 2 ratings" })
      ).toBeInTheDocument();
      expect(screen.getByRole("img", { name: "5 estrellas: 1 voto (50%)" })).toBeInTheDocument();
    });

    it("renders the rating input with the user's rating when actions are provided", () => {
      render(
        <CourseDetailComponent
          course={mockCourse}
          userRating={4}
          onRate={vi.fn()}
          onRemove={vi.fn()}
        />
      );

      expect(screen.getByRole("group", { name: "Califica este curso" })).toBeInTheDocument();
      expect(screen.getByRole("radio", { name: "4 estrellas" })).toBeChecked();
    });

    it("asks the user to sign in when there are no actions", () => {
      render(<CourseDetailComponent course={mockCourse} />);

      expect(screen.queryByRole("group", { name: "Califica este curso" })).not.toBeInTheDocument();
      expect(screen.getByText("Inicia sesión para calificar este curso.")).toBeInTheDocument();
    });

    it("renders 0.0 for a course without ratings", () => {
      const { container } = render(
        <CourseDetailComponent
          course={{ ...mockCourse, average_rating: 0, total_ratings: 0, rating_distribution: undefined }}
        />
      );

      expect(screen.getByRole("img", { name: "Rating: 0.0 out of 5 stars" })).toBeInTheDocument();
      expect(container.textContent).not.toMatch(/undefined|NaN/);
    });
  });
});
