// Logical asset manifest for the pixel-art debate replay — paths are relative
// to /public. Keep entries in sync with frontend/public/replay/.

export const ROOM_BG = '/replay/rooms/seminar-day.png';
export const TABLE_SPRITE = '/replay/rooms/seminar-table.png';

export type SpriteDirection = 'front-left' | 'front-right' | 'rear-left' | 'rear-right';
export type AgentSprite = 'advocate' | 'auditor' | 'assessor' | 'arbitrator' | 'gatekeeper';

export function getSpritePath(sprite: AgentSprite, direction: SpriteDirection): string {
  return `/replay/sprites/${sprite}-${direction}.png`;
}
