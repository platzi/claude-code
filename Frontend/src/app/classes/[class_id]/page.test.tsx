import { renderToString } from "react-dom/server";
import ClassPage from "./page";
import { ClassDetail } from "@/types";
import { describe, it, expect, vi } from "vitest";

vi.mock("@/components/VideoPlayer/VideoPlayer", () => ({
  VideoPlayer: ({ src, title }: { src: string; title: string }) => (
    <div data-testid="mock-video-player">
      {title} - {src}
    </div>
  ),
}));

const CLASS_DATA: ClassDetail = {
  id: 19,
  title: "Clase de Test",
  description: "Descripción de la clase de test",
  video: "https://test.com/video.mp4",
  duration: 1200,
  slug: "clase-test",
};

// Mock de fetch que resuelve inmediatamente
global.fetch = vi.fn().mockImplementation(async () =>
  new Response(JSON.stringify(CLASS_DATA), {
    status: 200,
    headers: { "content-type": "application/json" },
  })
);

describe("ClassPage", () => {
  it("renders class info and video", async () => {
    const html = renderToString(await ClassPage({ params: Promise.resolve({ class_id: "19" }) }));

    expect(html).toContain("Clase de Test");
    expect(html).toContain("Descripción de la clase de test");
    expect(html).toContain("mock-video-player");
    expect(html).toContain("Regresar al curso");
    expect(global.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/classes/19",
      expect.objectContaining({ method: "GET" })
    );
  }, 10000); // Aumentamos el timeout a 10 segundos
});
