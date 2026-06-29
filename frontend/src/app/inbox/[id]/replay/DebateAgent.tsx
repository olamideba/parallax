'use client';

import React from 'react';
import { AgentRole } from '@/lib/api';
import { getSpritePath } from '@/lib/replay/assets';
import { SEATS, ROLE_SEAT } from '@/lib/replay/seminarRoom';
import styles from './replay.module.css';

interface DebateAgentProps {
  role: AgentRole;
  speaking: boolean;
  hasSpoken: boolean;
  dot: string;
  speechText?: string;
  idleDelay?: number;
}

const SPRITE_HEIGHT = 78;

export default function DebateAgent({
  role,
  speaking,
  hasSpoken,
  dot,
  speechText,
  idleDelay = 0,
}: DebateAgentProps) {
  const { seatKey, sprite } = ROLE_SEAT[role];
  const seat = SEATS[seatKey];
  const spriteSrc = getSpritePath(sprite, seat.facing);

  return (
    <div
      className={styles.characterWrapper}
      style={{
        left: `${seat.x}%`,
        top: `${seat.y}%`,
        zIndex: seat.zIndex,
        opacity: hasSpoken || speaking ? 1 : 0.45,
      }}
    >
      {speaking && speechText && (
        <div className={styles.speechBubble} style={{ borderColor: `${dot}66` }}>
          {speechText.length > 110 ? `${speechText.slice(0, 110)}…` : speechText}
        </div>
      )}
      <div className={styles.charBodyGroup}>
        <div className={styles.charShadow} />
        <img
          src={spriteSrc}
          alt={role}
          draggable={false}
          className={`${styles.charSprite} ${speaking ? styles.active : ''}`}
          style={{
            height: SPRITE_HEIGHT,
            width: 'auto',
            animationDelay: `${idleDelay}s`,
            filter: speaking
              ? `drop-shadow(0 0 4px ${dot}) drop-shadow(0 0 1px #000)`
              : 'drop-shadow(0 1px 1px rgba(0,0,0,0.5))',
          }}
        />
      </div>
    </div>
  );
}
