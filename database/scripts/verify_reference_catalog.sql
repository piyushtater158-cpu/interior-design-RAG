-- Paste into Supabase → SQL Editor (or psql) to verify catalog constraints after migrations 013–015.
-- Expect: first query 0 rows; second and third only allowed values.

SELECT id, style_tags, cardinality(style_tags) AS n
FROM public.reference_images
WHERE style_tags IS NULL
   OR cardinality(style_tags) <> 1
   OR (style_tags)[1] NOT IN (
     'scandinavian', 'japandi', 'midcentury', 'traditional', 'industrial', 'boho'
   );

SELECT id, room_type
FROM public.reference_images
WHERE room_type IS NULL
   OR trim(room_type) = ''
   OR room_type NOT IN (
     'bedroom', 'kids room', 'dining room', 'kitchen', 'mandir', 'living room'
   );

SELECT (style_tags)[1] AS style_slug, count(*) AS n
FROM public.reference_images
GROUP BY 1
ORDER BY n DESC;

SELECT room_type, count(*) AS n
FROM public.reference_images
GROUP BY 1
ORDER BY n DESC;

-- RLS (migration 016): expect one SELECT policy for authenticated, owner-scoped writes.
SELECT policyname, cmd, roles::text, qual, with_check
FROM pg_policies
WHERE schemaname = 'public' AND tablename = 'reference_images'
ORDER BY policyname;
