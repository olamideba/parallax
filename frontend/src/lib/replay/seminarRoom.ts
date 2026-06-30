import { AgentRole } from '@/lib/api';
import { AgentSprite, SpriteDirection } from './assets';

export interface Seat {
  x: number;
  y: number;
  facing: SpriteDirection;
  zIndex: number;
}

// Table PNG is 1200×896 with the oval occupying roughly x[20%-90%] y[21%-89%].
// Rendered at 50% of the stage container width and positioned so the oval
// center lands at (50%, 58%) of the stage. Opaque oval in stage-% coords:
//   x[32.3%-67.7%]  y[41.1%-74.9%]
export const TABLE_CSS = {
  left: 22.4,   // % of container
  top: 30.4,    // % of container
  width: 50,    // % of container
  zIndex: 60,   // midpoint of y-range; agents with y%>60 render in front
};

// All coordinates are % of the 1200×896 stage canvas; values mark character FEET.
// transform: translate(-50%, -100%) in the renderer maps the coordinate to foot position.
// z-index = round(y%) keeps isometric depth order: higher y = closer to viewer.
//
// Layout: 2 agents left of the oval long edge (face right → front-right)
//         2 agents right of the oval long edge (face left → front-left)
//         1 agent at the near narrow end / head (face into room → rear-right)
export const SEATS: Record<string, Seat> = {
  'head':        { x: 50.0, y: 79.6, facing: 'rear-right',  zIndex: 80 },
  'left-upper':  { x: 26.9, y: 50.4, facing: 'front-right', zIndex: 50 },
  'left-lower':  { x: 27.8, y: 64.1, facing: 'front-right', zIndex: 64 },
  'right-upper': { x: 70.2, y: 50.4, facing: 'front-left',  zIndex: 50 },
  'right-lower': { x: 69.5, y: 64.1, facing: 'front-left',  zIndex: 64 },
};

export const ROLE_SEAT: Record<AgentRole, { seatKey: keyof typeof SEATS; sprite: AgentSprite }> = {
  arbitrator: { seatKey: 'head',        sprite: 'arbitrator' },
  advocate:   { seatKey: 'left-upper',  sprite: 'advocate'   },
  assessor:   { seatKey: 'left-lower',  sprite: 'assessor'   },
  auditor:    { seatKey: 'right-upper', sprite: 'auditor'    },
  gatekeeper: { seatKey: 'right-lower', sprite: 'gatekeeper' },
};
