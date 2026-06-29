import { AgentRole } from '@/lib/api';
import { AgentSprite, SpriteDirection } from './assets';

export interface Seat {
  x: number;
  y: number;
  facing: SpriteDirection;
  zIndex: number;
}

// Coordinates measured from the actual 1200×896 room canvas, converted to %.
// Dots mark character FEET (transform: translate(-50%,-100%) in the renderer).
// Verified by compositing onto the room image and viewing the result.
export const SEATS: Record<string, Seat> = {
  // Left curved end — only viable "head" (right end = bookshelf wall, no floor)
  'seat-head':   { x: 18.3, y: 52.5, facing: 'front-right', zIndex: 53 },
  // Near long side, left third
  'seat-left':   { x: 25.8, y: 73.7, facing: 'front-right', zIndex: 74 },
  // Near long side, center
  'seat-center': { x: 44.2, y: 73.7, facing: 'front-left',  zIndex: 74 },
  // Near long side, right third
  'seat-right':  { x: 60.8, y: 72.0, facing: 'front-left',  zIndex: 72 },
  // Left wall — gatekeeper cameo, not at the table
  door:          { x: 7.5,  y: 64.2, facing: 'front-right', zIndex: 64 },
};

export const ROLE_SEAT: Record<AgentRole, { seatKey: keyof typeof SEATS; sprite: AgentSprite }> = {
  arbitrator: { seatKey: 'seat-head',   sprite: 'arbitrator' },
  advocate:   { seatKey: 'seat-left',   sprite: 'advocate'   },
  assessor:   { seatKey: 'seat-center', sprite: 'assessor'   },
  auditor:    { seatKey: 'seat-right',  sprite: 'auditor'    },
  gatekeeper: { seatKey: 'door',        sprite: 'gatekeeper' },
};
