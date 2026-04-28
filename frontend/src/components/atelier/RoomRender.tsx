import type { CSSProperties } from 'react';
import { TOKENS, type RoomTone } from '@/lib/tokens';
import { IsoRoom } from './IsoRoom';
import { Anno } from './Anno';

type IsoType = 'bedroom' | 'dining' | 'kitchen' | 'mandir' | 'living';

type Props = {
  type?: IsoType;
  tone?: RoomTone;
  size?: number;
  label?: string;
  anno?: string;
  /** Optional URL to a real generated image. When present, replaces the procedural IsoRoom. */
  imageUrl?: string | null;
  className?: string;
  style?: CSSProperties;
};

export function RoomRender({
  type = 'bedroom',
  tone = 'warm',
  size = 520,
  label,
  anno,
  imageUrl,
  className = '',
  style,
}: Props) {
  return (
    <div
      className={`relative w-full h-full overflow-hidden flex items-center justify-center ${className}`}
      style={{
        background: `linear-gradient(145deg, ${TOKENS.paper} 0%, ${TOKENS.bone} 60%, ${TOKENS.boneDeep} 100%)`,
        ...style,
      }}
    >
      {imageUrl ? (
        /* eslint-disable-next-line @next/next/no-img-element */
        <img src={imageUrl} alt={label ?? type} className="absolute inset-0 w-full h-full object-cover" />
      ) : (
        <>
          <div
            className="absolute inset-0"
            style={{
              backgroundImage:
                'radial-gradient(circle at 1px 1px, rgba(28,27,23,0.07) 1px, transparent 0)',
              backgroundSize: '24px 24px',
              maskImage: 'radial-gradient(ellipse at center, black 40%, transparent 75%)',
              WebkitMaskImage: 'radial-gradient(ellipse at center, black 40%, transparent 75%)',
            }}
          />
          <IsoRoom type={type} size={size} tone={tone} style={{ position: 'relative', zIndex: 1 }} />
        </>
      )}
      {anno && (
        <div className="absolute top-4 left-4 z-10">
          <Anno>{anno}</Anno>
        </div>
      )}
      {label && (
        <div className="absolute bottom-4 left-4 z-10">
          <Anno color={TOKENS.inkSoft}>{label}</Anno>
        </div>
      )}
    </div>
  );
}
