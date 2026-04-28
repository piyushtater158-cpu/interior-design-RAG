import { Suspense } from 'react';
import { NewSession } from '@/components/screens/NewSession';

export default function Page() {
  return (
    <Suspense fallback={null}>
      <NewSession />
    </Suspense>
  );
}
