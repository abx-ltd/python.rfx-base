ALTER TABLE "rfx_user"."invitation"
DROP COLUMN "profile_id";

ALTER TABLE "rfx_user"."invitation"
ADD COLUMN "profile_id" UUID REFERENCES "rfx_user"."profile"("_id");

ALTER TABLE "rfx_user"."invitation"
ADD COLUMN "sender_id" UUID NOT NULL REFERENCES "rfx_user"."user"("_id");
