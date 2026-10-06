import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { RatingInput } from "../RatingInput";
import type { ActionResult } from "@/types/rating";

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((res) => {
    resolve = res;
  });
  return { promise, resolve };
}

function setup(initialRating: number | null = null) {
  const onRate = vi.fn(
    async (rating: number): Promise<ActionResult> => ({ ok: true, rating })
  );
  const onRemove = vi.fn(async (): Promise<ActionResult> => ({ ok: true, rating: null }));
  const user = userEvent.setup();
  const utils = render(
    <RatingInput initialRating={initialRating} onRate={onRate} onRemove={onRemove} />
  );
  return { user, onRate, onRemove, ...utils };
}

describe("RatingInput", () => {
  it("renders a labelled group of 5 radios with accessible names", () => {
    setup();

    expect(screen.getByRole("group", { name: "Califica este curso" })).toBeInTheDocument();
    const radios = screen.getAllByRole("radio");
    expect(radios).toHaveLength(5);
    expect(screen.getByRole("radio", { name: "1 estrella" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "5 estrellas" })).toBeInTheDocument();
  });

  it("reflects initialRating", () => {
    setup(3);

    expect(screen.getByRole("radio", { name: "3 estrellas" })).toBeChecked();
    expect(screen.getByText("Tu calificación: 3 de 5")).toBeInTheDocument();
  });

  it("shows no selection and no remove button when the user has not rated", () => {
    setup(null);

    screen.getAllByRole("radio").forEach((radio) => expect(radio).not.toBeChecked());
    expect(screen.getByText("Aún no has calificado este curso")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Quitar calificación" })).not.toBeInTheDocument();
  });

  it("calls onRate with the clicked value and announces success", async () => {
    const { user, onRate } = setup();

    await user.click(screen.getByRole("radio", { name: "4 estrellas" }));

    expect(onRate).toHaveBeenCalledWith(4);
    expect(await screen.findByRole("status")).toHaveTextContent("Guardado: 4 estrellas.");
    expect(screen.getByRole("radio", { name: "4 estrellas" })).toBeChecked();
  });

  it("moves the selection with the arrow keys", async () => {
    const { user, onRate } = setup(3);

    screen.getByRole("radio", { name: "3 estrellas" }).focus();
    await user.keyboard("{ArrowRight}");

    expect(onRate).toHaveBeenLastCalledWith(4);
    await waitFor(() =>
      expect(screen.getByRole("radio", { name: "4 estrellas" })).toBeChecked()
    );
    expect(screen.getByRole("radio", { name: "4 estrellas" })).toHaveFocus();
  });

  it("shows the optimistic value while the action is pending", async () => {
    const pending = deferred<ActionResult>();
    const onRate = vi.fn(() => pending.promise);
    const user = userEvent.setup();
    render(<RatingInput initialRating={2} onRate={onRate} onRemove={vi.fn()} />);

    await user.click(screen.getByRole("radio", { name: "5 estrellas" }));

    expect(screen.getByRole("radio", { name: "5 estrellas" })).toBeChecked();
    expect(screen.getByRole("group")).toHaveAttribute("aria-busy", "true");

    pending.resolve({ ok: true, rating: 5 });
    await waitFor(() => expect(screen.getByRole("group")).toHaveAttribute("aria-busy", "false"));
    expect(screen.getByRole("radio", { name: "5 estrellas" })).toBeChecked();
  });

  it("rolls back and shows the error when the action fails", async () => {
    const onRate = vi.fn(
      async (): Promise<ActionResult> => ({ ok: false, error: "No pudimos guardar." })
    );
    const user = userEvent.setup();
    render(<RatingInput initialRating={2} onRate={onRate} onRemove={vi.fn()} />);

    await user.click(screen.getByRole("radio", { name: "5 estrellas" }));

    expect(await screen.findByRole("status")).toHaveTextContent("No pudimos guardar.");
    expect(screen.getByRole("radio", { name: "2 estrellas" })).toBeChecked();
    expect(screen.getByRole("radio", { name: "5 estrellas" })).not.toBeChecked();
  });

  it("removes the rating with the remove button", async () => {
    const { user, onRemove } = setup(4);

    await user.click(screen.getByRole("button", { name: "Quitar calificación" }));

    expect(onRemove).toHaveBeenCalledTimes(1);
    expect(await screen.findByRole("status")).toHaveTextContent("Calificación eliminada.");
    screen.getAllByRole("radio").forEach((radio) => expect(radio).not.toBeChecked());
    expect(screen.queryByRole("button", { name: "Quitar calificación" })).not.toBeInTheDocument();
  });

  it("syncs with a new initialRating from the server", () => {
    const props = { onRate: vi.fn(), onRemove: vi.fn() };
    const { rerender } = render(<RatingInput initialRating={1} {...props} />);

    rerender(<RatingInput initialRating={5} {...props} />);

    expect(screen.getByRole("radio", { name: "5 estrellas" })).toBeChecked();
  });
});
