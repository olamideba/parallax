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

// Measured center of the tabletop surface (stage %) — speakers lean toward it.
export const TABLE_CENTER = { x: 47.5, y: 52.3 };

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
// Geometry measured from the table PNG's opaque pixels (scripted, not eyeballed):
// tabletop major axis runs from the FAR tip at (32.3%, 46.5%) [upper-left, by
// the windows] to the NEAR tip at (62.5%, 58.2%) [lower-right, toward camera];
// rear-edge peak (39.3%, 41.1%); surface center ≈ (47.5%, 52.3%).
// Each seat marks the agent's FEET, offset just outside the tabletop edge.
export const SEATS: Record<string, Seat> = {
  'head-far':  { x: 34.4, y: 44.9, facing: 'front-left', zIndex: 45 }, // arbitrator, far (upper-left) tip
  'foot-near': { x: 63.0, y: 70.2, facing: 'rear-right',   zIndex: 70 }, // advocate, near (lower-right) tip
  'side-rear': { x: 52.0, y: 47.8, facing: 'front-right',  zIndex: 48 }, // auditor, rear long edge (by whiteboard)
  'side-near': { x: 41.0, y: 63.5, facing: 'rear-left',  zIndex: 64 }, // assessor, front long edge (opposite)
  'room-edge': { x: 14.0, y: 62.0, facing: 'front-left', zIndex: 62 }, // gatekeeper, off-table by extinguisher
};

export const ROLE_SEAT: Record<AgentRole, { seatKey: keyof typeof SEATS; sprite: AgentSprite }> = {
  arbitrator: { seatKey: 'head-far',  sprite: 'arbitrator' },
  advocate:   { seatKey: 'foot-near', sprite: 'advocate'   },
  auditor:    { seatKey: 'side-rear', sprite: 'auditor'    },
  assessor:   { seatKey: 'side-near', sprite: 'assessor'   },
  gatekeeper: { seatKey: 'room-edge', sprite: 'gatekeeper' },
};
