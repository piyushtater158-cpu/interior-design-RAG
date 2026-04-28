import { Export } from '@/components/screens/Export';

export default function Page({ params }: { params: { sessionId: string } }) {
  return <Export sessionId={params.sessionId} />;
}
