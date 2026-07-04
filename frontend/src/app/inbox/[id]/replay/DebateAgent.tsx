'use client';

import React from 'react';
import { AgentRole } from '@/lib/api';
import { getSpritePath, SpriteDirection } from '@/lib/replay/assets';
import { SEATS, ROLE_SEAT, TABLE_CENTER } from '@/lib/replay/seminarRoom';
import styles from './replay.module.css';

interface DebateAgentProps {
  role: AgentRole;
  speaking: boolean;
  /** The active speaker cited this agent's earlier turn — do a reaction hop. */
  referenced: boolean;
  /** Which way to face right now (listeners turn toward the speaker). */
  facing: SpriteDirection;
  dot: string;
  /** Stagger for the one-shot entrance drop-in. */
  entranceIndex?: number;
}

const SPRITE_HEIGHT = 96;

export default function DebateAgent({
  role,
  speaking,
  referenced,
  facing,
  dot,
  entranceIndex = 0,
}: DebateAgentProps) {
  const { seatKey, sprite } = ROLE_SEAT[role];
  const seat = SEATS[seatKey];
  const spriteSrc = getSpritePath(sprite, facing);
  // Speaking agents take a small step toward the table — unit vector to center.
  const dx = TABLE_CENTER.x - seat.x;
  const dy = TABLE_CENTER.y - seat.y;
  const len = Math.hypot(dx, dy) || 1;
  const stepTransform = speaking
    ? `translate(${((dx / len) * 8).toFixed(1)}px, ${((dy / len) * 5).toFixed(1)}px) scale(1.07)`
    : undefined;

  return (
    <div
      className={styles.characterWrapper}
      style={{
        left: `${seat.x}%`,
        top: `${seat.y}%`,
        zIndex: speaking ? seat.zIndex + 100 : seat.zIndex,
      }}
    >
      <div
        className={`${styles.charBodyGroup} ${speaking ? styles.speaking : ''}`}
        style={{ animationDelay: `${entranceIndex * 0.12}s`, transform: stepTransform }}
      >
        {speaking && <div className={styles.spotlight} style={{ background: dot }} />}
        <div className={styles.charShadow} />
        <div className={`${styles.spriteMotion} ${referenced ? styles.referenced : ''}`}>
          <img
            src={spriteSrc}
            alt={role}
            draggable={false}
            className={`${styles.charSprite} ${speaking ? styles.active : ''}`}
            style={{
              height: SPRITE_HEIGHT,
              width: 'auto',
              // Varied idle rhythm so the room never bobs in unison.
              animationDelay: `${entranceIndex * 0.45}s`,
              animationDuration: speaking ? undefined : `${2.7 + entranceIndex * 0.35}s`,
              filter: speaking
                ? `drop-shadow(0 0 5px ${dot}) drop-shadow(0 0 1px #000)`
                : 'drop-shadow(0 1px 1px rgba(0,0,0,0.5))',
            }}
          />
        </div>
      </div>
    </div>
  );
}
