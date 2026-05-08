'use client';

import { useRouter } from 'next/navigation';
import { AtelierMark } from '@/components/atelier/AtelierMark';
import { BlueprintBg } from '@/components/atelier/BlueprintBg';
import { Btn } from '@/components/atelier/Btn';
import { Anno } from '@/components/atelier/Anno';

export function Landing() {
  const router = useRouter();

  return (
    <BlueprintBg className="min-h-screen flex items-center justify-center px-6">
      <div className="max-w-xl w-full flex flex-col items-center text-center gap-8">
        <div className="flex items-center gap-3">
          <AtelierMark size={40} />
          <div className="font-serif text-[30px] leading-none">Atelier</div>
        </div>
        <Anno>interior design studio · MVP</Anno>
        <h1 className="font-serif text-[44px] md:text-[56px] leading-[1.05] text-ink">
          Upload a room. <em className="font-serif italic">Describe a mood.</em> <br />
          Get a draft in seconds.
        </h1>
        <p className="text-ink-soft text-base max-w-md">
          An AI design assistant tuned for studios. Draft, iterate, commit — without leaving the conversation.
        </p>
        <div className="flex items-center gap-3 pt-2">
          <Btn size="lg" onClick={() => router.push('/signin')}>
            Sign in to start
          </Btn>
        </div>
        <Anno className="pt-6">phase 3 · responsive · ipad + desktop</Anno>
      </div>
    </BlueprintBg>
  );
}
