import { Canvas } from '@/components/screens/Canvas';

export default function Page({ params }: { params: { sessionId: string } }) {
  return <Canvas sessionId={params.sessionId} />;
}
