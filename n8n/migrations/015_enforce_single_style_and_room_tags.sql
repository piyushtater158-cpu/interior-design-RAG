-- Migration 015: enforce exactly one style_tag and one valid room_type
-- style_tags: must be NOT NULL, exactly 1 element, and from the valid vocabulary
-- room_type:  must be NOT NULL and from the valid vocabulary

BEGIN;

-- 1. style_tags: drop the permissive default, enforce NOT NULL
ALTER TABLE reference_images
  ALTER COLUMN style_tags DROP DEFAULT,
  ALTER COLUMN style_tags SET NOT NULL;

-- 2. room_type: enforce NOT NULL
ALTER TABLE reference_images
  ALTER COLUMN room_type SET NOT NULL;

-- 3. Exactly one style tag (cardinality works correctly on empty arrays: returns 0, not NULL)
ALTER TABLE reference_images
  ADD CONSTRAINT chk_style_tags_single
    CHECK (cardinality(style_tags) = 1);

-- 4. Style tag must be one of the six UI styles
ALTER TABLE reference_images
  ADD CONSTRAINT chk_style_tag_valid
    CHECK (style_tags[1] IN ('scandinavian','japandi','midcentury','traditional','industrial','boho'));

-- 5. Room type must be one of the six valid room types
ALTER TABLE reference_images
  ADD CONSTRAINT chk_room_type_valid
    CHECK (room_type IN ('bedroom','kids room','dining room','kitchen','mandir','living room'));

COMMIT;
