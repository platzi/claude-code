import { render, screen } from "@testing-library/react";
import { VideoPlayer, VideoPlayerProps } from "./VideoPlayer";

// Si usas Vitest, descomenta la siguiente línea:
// import { describe, it, expect } from 'vitest';

describe("VideoPlayer", () => {
  const mockProps: VideoPlayerProps = {
    src: "https://test.com/video.mp4",
    title: "Clase de prueba",
  };

  it("renders the video element", () => {
    render(<VideoPlayer {...mockProps} />);
    const video = screen.getByTestId("video-element");
    expect(video).toBeInTheDocument();
  });

  it("renders the correct video source", () => {
    render(<VideoPlayer {...mockProps} />);
    const source = screen.getByTestId("video-element").querySelector("source");
    expect(source).toHaveAttribute("src", mockProps.src);
  });

  it("renders the title as fallback text", () => {
    render(<VideoPlayer {...mockProps} />);
    expect(screen.getByText(mockProps.title)).toBeInTheDocument();
  });
});
