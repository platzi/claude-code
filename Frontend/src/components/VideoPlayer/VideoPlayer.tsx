import { FC } from "react";
import styles from "./VideoPlayer.module.scss";

export interface VideoPlayerProps {
  src: string;
  title: string;
}

export const VideoPlayer: FC<VideoPlayerProps> = ({ src, title }) => {
  return (
    <div className={styles.videoPlayer}>
      <video controls className={styles.video} data-testid="video-element">
        <source src={src} type="video/mp4" />
        {title}
      </video>
    </div>
  );
};
