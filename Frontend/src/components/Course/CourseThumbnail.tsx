'use client';

import { useState } from 'react';
import styles from './Course.module.scss';

const TECH_COLORS: Record<string, string> = {
  react:      'linear-gradient(135deg, #61dafb 0%, #21a1f1 100%)',
  python:     'linear-gradient(135deg, #3572A5 0%, #1e3f6e 100%)',
  javascript: 'linear-gradient(135deg, #f7df1e 0%, #e6b800 100%)',
  typescript: 'linear-gradient(135deg, #3178c6 0%, #1a4a8a 100%)',
  'vue.js':   'linear-gradient(135deg, #42b883 0%, #2d8a5f 100%)',
  'node.js':  'linear-gradient(135deg, #68a063 0%, #3d6b39 100%)',
  docker:     'linear-gradient(135deg, #2496ed 0%, #1565c0 100%)',
  css:        'linear-gradient(135deg, #264de4 0%, #1a32a0 100%)',
  angular:    'linear-gradient(135deg, #dd0031 0%, #9a0020 100%)',
};

function getGradient(name: string): string {
  const lower = name.toLowerCase();
  for (const key of Object.keys(TECH_COLORS)) {
    if (lower.includes(key)) return TECH_COLORS[key];
  }
  return 'linear-gradient(135deg, #ff2d2d 0%, #9b0000 100%)';
}

function getInitials(name: string): string {
  return name
    .replace(/^Curso de /i, '')
    .split(' ')
    .slice(0, 2)
    .map((w) => w[0])
    .join('')
    .toUpperCase();
}

interface CourseThumbnailProps {
  src: string;
  alt: string;
  name: string;
}

export function CourseThumbnail({ src, alt, name }: CourseThumbnailProps) {
  const [error, setError] = useState(false);

  if (error) {
    return (
      <div
        className={styles.thumbnailFallback}
        style={{ background: getGradient(name) }}
        aria-label={alt}
      >
        <span className={styles.thumbnailInitials}>{getInitials(name)}</span>
        <span className={styles.thumbnailName}>{name.replace(/^Curso de /i, '')}</span>
      </div>
    );
  }

  return (
    <img
      src={src}
      alt={alt}
      className={styles.thumbnail}
      onError={() => setError(true)}
    />
  );
}
