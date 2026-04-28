import type { CSSProperties } from 'react';
import type { RoomTone } from '@/lib/tokens';

type IsoType = 'bedroom' | 'dining' | 'kitchen' | 'mandir' | 'living';

type Palette = { floor: string; wall: string; wallDk: string; obj: string; accent: string };

const PALETTES: Record<RoomTone, Palette> = {
  warm: { floor: '#E8DCC2', wall: '#D8C9AE', wallDk: '#C6B593', obj: '#6B4E2A', accent: '#B85C3A' },
  cool: { floor: '#D6DAD3', wall: '#C5CAC1', wallDk: '#AEB4A8', obj: '#3D4A2A', accent: '#6B7B5A' },
  moody: { floor: '#9B9386', wall: '#7A7569', wallDk: '#5E5A4E', obj: '#2A2620', accent: '#B85C3A' },
};

export function IsoRoom({
  type = 'bedroom',
  size = 200,
  tone = 'warm',
  style,
}: {
  type?: IsoType;
  size?: number;
  tone?: RoomTone;
  style?: CSSProperties;
}) {
  const p = PALETTES[tone] ?? PALETTES.warm;
  const W = size;
  const H = size;

  const iso = (x: number, y: number, z: number): [number, number] => {
    const cx = W / 2;
    const cy = H * 0.72;
    const sx = cx + (x - y) * (W * 0.22);
    const sy = cy + (x + y) * (W * 0.11) - z * (W * 0.18);
    return [sx, sy];
  };

  const polyPoints = (pts: [number, number, number][]) =>
    pts.map((pt) => iso(...pt).join(',')).join(' ');

  const poly = (pts: [number, number, number][], fill: string, opacity = 1, key?: string) => (
    <polygon key={key} points={polyPoints(pts)} fill={fill} opacity={opacity} />
  );

  const isoX = (x: number, y: number, z: number) => iso(x, y, z)[0];
  const isoY = (x: number, y: number, z: number) => iso(x, y, z)[1];

  const objects: Record<IsoType, JSX.Element> = {
    bedroom: (
      <g>
        {poly([[-0.7, -0.3, 0], [0.7, -0.3, 0], [0.7, 0.5, 0], [-0.7, 0.5, 0]], p.obj, 0.25, 'b1')}
        {poly([[-0.7, -0.3, 0.25], [0.7, -0.3, 0.25], [0.7, 0.5, 0.25], [-0.7, 0.5, 0.25]], p.obj, 1, 'b2')}
        {poly([[-0.7, -0.3, 0.25], [0.7, -0.3, 0.25], [0.7, -0.3, 0], [-0.7, -0.3, 0]], p.obj, 0.75, 'b3')}
        {poly([[0.7, -0.3, 0.25], [0.7, 0.5, 0.25], [0.7, 0.5, 0], [0.7, -0.3, 0]], p.obj, 0.55, 'b4')}
        {poly([[-0.6, -0.2, 0.32], [0.6, -0.2, 0.32], [0.6, 0, 0.32], [-0.6, 0, 0.32]], '#F4EFE6', 1, 'b5')}
        {poly([[-1.05, -0.3, 0.35], [-0.75, -0.3, 0.35], [-0.75, 0, 0.35], [-1.05, 0, 0.35]], p.accent, 1, 'b6')}
        {poly([[-1.05, -0.3, 0.35], [-0.75, -0.3, 0.35], [-0.75, -0.3, 0], [-1.05, -0.3, 0]], p.accent, 0.75, 'b7')}
        <circle cx={isoX(-0.9, -0.15, 0.55)} cy={isoY(-0.9, -0.15, 0.55)} r={size * 0.035} fill={p.accent} opacity="0.95" />
      </g>
    ),
    dining: (
      <g>
        {poly([[-0.8, -0.5, 0.4], [0.8, -0.5, 0.4], [0.8, 0.5, 0.4], [-0.8, 0.5, 0.4]], p.obj, 1, 'd1')}
        {poly([[-0.8, -0.5, 0.4], [0.8, -0.5, 0.4], [0.8, -0.5, 0.38], [-0.8, -0.5, 0.38]], p.obj, 0.7, 'd2')}
        {poly([[-0.5, -0.95, 0], [-0.2, -0.95, 0], [-0.2, -0.65, 0], [-0.5, -0.65, 0]], p.accent, 0.3, 'd3')}
        {poly([[-0.5, -0.95, 0.25], [-0.2, -0.95, 0.25], [-0.2, -0.65, 0.25], [-0.5, -0.65, 0.25]], p.accent, 1, 'd4')}
        {poly([[0.2, -0.95, 0.25], [0.5, -0.95, 0.25], [0.5, -0.65, 0.25], [0.2, -0.65, 0.25]], p.accent, 1, 'd5')}
        <line x1={isoX(0, 0, 1.4)} y1={isoY(0, 0, 1.4)} x2={isoX(0, 0, 0.9)} y2={isoY(0, 0, 0.9)} stroke={p.obj} strokeWidth="1" />
        <circle cx={isoX(0, 0, 0.9)} cy={isoY(0, 0, 0.9)} r={size * 0.04} fill={p.accent} />
      </g>
    ),
    kitchen: (
      <g>
        {poly([[-1, -0.4, 0], [1, -0.4, 0], [1, -0.1, 0], [-1, -0.1, 0]], p.obj, 0.25, 'k1')}
        {poly([[-1, -0.4, 0.5], [1, -0.4, 0.5], [1, -0.1, 0.5], [-1, -0.1, 0.5]], p.wall, 1, 'k2')}
        {poly([[-1, -0.4, 0], [-1, -0.4, 0.5], [1, -0.4, 0.5], [1, -0.4, 0]], p.wallDk, 0.85, 'k3')}
        {poly([[-1, -0.4, 1.1], [1, -0.4, 1.1], [1, -0.4, 0.85], [-1, -0.4, 0.85]], p.obj, 0.6, 'k4')}
        {poly([[-1, -0.4, 1.1], [1, -0.4, 1.1], [1, -0.1, 1.1], [-1, -0.1, 1.1]], p.obj, 0.35, 'k5')}
        {poly([[-0.4, 0.5, 0.5], [0.4, 0.5, 0.5], [0.4, 0.8, 0.5], [-0.4, 0.8, 0.5]], p.accent, 1, 'k6')}
        {poly([[-0.4, 0.5, 0], [0.4, 0.5, 0], [0.4, 0.5, 0.5], [-0.4, 0.5, 0.5]], p.accent, 0.7, 'k7')}
      </g>
    ),
    mandir: (
      <g>
        {poly([[-0.7, -0.3, 0], [0.7, -0.3, 0], [0.7, 0.5, 0], [-0.7, 0.5, 0]], p.accent, 0.35, 'm1')}
        {poly([[-0.7, -0.3, 0.15], [0.7, -0.3, 0.15], [0.7, 0.5, 0.15], [-0.7, 0.5, 0.15]], p.accent, 1, 'm2')}
        {poly([[-0.7, -0.3, 0.15], [0.7, -0.3, 0.15], [0.7, -0.3, 0], [-0.7, -0.3, 0]], p.accent, 0.7, 'm3')}
        {poly([[-0.5, -0.3, 0.15], [-0.5, -0.3, 1.1], [0.5, -0.3, 1.1], [0.5, -0.3, 0.15]], p.obj, 0.75, 'm4')}
        <path
          d={`M ${iso(-0.5, -0.3, 1.1).join(',')} Q ${iso(0, -0.3, 1.35).join(',')} ${iso(0.5, -0.3, 1.1).join(',')}`}
          fill="none"
          stroke={p.obj}
          strokeWidth="2"
        />
        <circle cx={isoX(0, 0.1, 0.2)} cy={isoY(0, 0.1, 0.2)} r={size * 0.035} fill="#E8A040" />
      </g>
    ),
    living: (
      <g>
        {poly([[-0.9, -0.1, 0], [0.9, -0.1, 0], [0.9, 0.5, 0], [-0.9, 0.5, 0]], p.obj, 0.25, 'l1')}
        {poly([[-0.9, -0.1, 0.28], [0.9, -0.1, 0.28], [0.9, 0.5, 0.28], [-0.9, 0.5, 0.28]], p.obj, 1, 'l2')}
        {poly([[-0.9, -0.1, 0.6], [0.9, -0.1, 0.6], [0.9, -0.1, 0.28], [-0.9, -0.1, 0.28]], p.obj, 0.7, 'l3')}
        {poly([[-0.3, 0.6, 0.15], [0.3, 0.6, 0.15], [0.3, 0.9, 0.15], [-0.3, 0.9, 0.15]], p.accent, 1, 'l4')}
        {poly([[-1, 0.55, 0], [1, 0.55, 0], [1, 1, 0], [-1, 1, 0]], p.accent, 0.25, 'l5')}
      </g>
    ),
  };

  return (
    <svg width={size} height={size} viewBox={`0 0 ${W} ${H}`} style={{ display: 'block', ...style }}>
      {poly([[-1.2, -1.2, 0], [1.2, -1.2, 0], [1.2, 1.2, 0], [-1.2, 1.2, 0]], p.floor, 1, 'floor')}
      {poly([[-1.2, -1.2, 0], [1.2, -1.2, 0], [1.2, -1.2, 1.4], [-1.2, -1.2, 1.4]], p.wallDk, 0.85, 'wall1')}
      {poly([[-1.2, -1.2, 0], [-1.2, 1.2, 0], [-1.2, 1.2, 1.4], [-1.2, -1.2, 1.4]], p.wall, 1, 'wall2')}
      {[-0.6, 0, 0.6].map((t, i) => (
        <line
          key={'h' + i}
          x1={isoX(t, -1.2, 0)}
          y1={isoY(t, -1.2, 0)}
          x2={isoX(t, 1.2, 0)}
          y2={isoY(t, 1.2, 0)}
          stroke={p.wallDk}
          strokeWidth="0.5"
          opacity="0.4"
        />
      ))}
      {[-0.6, 0, 0.6].map((t, i) => (
        <line
          key={'v' + i}
          x1={isoX(-1.2, t, 0)}
          y1={isoY(-1.2, t, 0)}
          x2={isoX(1.2, t, 0)}
          y2={isoY(1.2, t, 0)}
          stroke={p.wallDk}
          strokeWidth="0.5"
          opacity="0.4"
        />
      ))}
      {objects[type] ?? objects.bedroom}
    </svg>
  );
}
