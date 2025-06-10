import { renderToString } from "react-dom/server";
import { startTransition } from "react";
import ClassPage from "./page";
import { Class } from "@/types";
import { describe, it, expect, vi } from "vitest";

vi.mock("@/components/VideoPlayer/VideoPlayer", () => ({
  VideoPlayer: ({ src, title }: { src: string; title: string }) => (
    <div data-testid="mock-video-player">
      {title} - {src}
    </div>
  ),
}));

// Mock de fetch que resuelve inmediatamente
global.fetch = vi.fn().mockResolvedValue({
  ok: true,
  json: () =>
    Promise.resolve({
      id: 19,
      title: "Clase de Test",
      description: "Descripción de la clase de test",
      video: "https://test.com/video.mp4",
      duration: 1200,
      slug: "clase-test",
    } as Class),
});

describe("ClassPage", () => {
  it("renders class info and video", async () => {
    const html = await renderToString(<ClassPage params={{ class_id: "19" }} />);

    expect(html).toContain("Clase de Test");
    expect(html).toContain("Descripción de la clase de test");
    expect(html).toContain("mock-video-player");
    expect(html).toContain("Regresar al curso");
  }, 10000); // Aumentamos el timeout a 10 segundos
});
