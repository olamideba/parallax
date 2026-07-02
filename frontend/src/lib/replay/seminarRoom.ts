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
// The table renders at zIndex 60: seats with zIndex < 60 stand behind it,
// > 60 in front of it.
//
// The oval's major axis runs diagonally (iso view): near/foot tip at lower-left
// (~32%, 62%), far/head tip at upper-right (~70%, 47%). Long sides are the
// upper-left edge (rear) and lower-right edge (near).
//
// Layout — a tribunal around the table, gatekeeper off-table at the door side:
//   head-far:   far (upper-right) end — the Arbitrator presides
//   foot-near:  near (lower-left) end — the Advocate, opposite the Arbitrator
//   side-rear:  upper-left long side — the Auditor
//   side-near:  lower-right long side — the Assessor, opposite the Auditor
//   room-edge:  floor's left corner by the fire extinguisher — the Gatekeeper
//               (pre-filter, not a debater — visibly outside the tribunal)
export const SEATS: Record<string, Seat> = {
  'head-far':  { x: 71.5, y: 48.0, facing: 'front-left',  zIndex: 48 },
  'foot-near': { x: 28.5, y: 72.0, facing: 'rear-right',  zIndex: 72 },
  'side-rear': { x: 44.0, y: 45.5, facing: 'front-right', zIndex: 46 },
  'side-near': { x: 60.0, y: 74.0, facing: 'rear-left',   zIndex: 74 },
  'room-edge': { x: 11.0, y: 64.0, facing: 'front-right', zIndex: 64 },
};

export const ROLE_SEAT: Record<AgentRole, { seatKey: keyof typeof SEATS; sprite: AgentSprite }> = {
  arbitrator: { seatKey: 'head-far',  sprite: 'arbitrator' },
  advocate:   { seatKey: 'foot-near', sprite: 'advocate'   },
  auditor:    { seatKey: 'side-rear', sprite: 'auditor'    },
  assessor:   { seatKey: 'side-near', sprite: 'assessor'   },
  gatekeeper: { seatKey: 'room-edge', sprite: 'gatekeeper' },
};
