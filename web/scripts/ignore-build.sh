#!/bin/sh
# Vercel "Ignored Build Step", run from web/ (the project's Root Directory).
# Exit 0 skips the deploy; exit 1 builds it. Build only if something under web/ changed since the
# last deployed commit. With no previous deploy, or a commit git cannot find, build.
if [ -z "$VERCEL_GIT_PREVIOUS_SHA" ]; then
  exit 1
fi
if git diff --quiet "$VERCEL_GIT_PREVIOUS_SHA" HEAD -- . 2>/dev/null; then
  exit 0
fi
exit 1
