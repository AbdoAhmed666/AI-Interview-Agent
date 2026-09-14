# Frontend image for the AI Interview Agent UI.
#
# Build context is this directory:
#     docker build -t ai-interview-frontend ./frontend

# --------------------------------------------------------------------------
# Dependencies. Cached on the lockfile alone, so editing source does not
# reinstall node_modules.
# --------------------------------------------------------------------------
FROM node:22-alpine AS deps

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

# --------------------------------------------------------------------------
# Build.
# --------------------------------------------------------------------------
FROM node:22-alpine AS builder

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# NEXT_PUBLIC_* values are inlined into the client bundle during the build, so
# this is the URL the BROWSER will use to reach the API - not an address on the
# compose network. It cannot be changed after the image is built.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

RUN npm run build

# --------------------------------------------------------------------------
# Runtime: the standalone server plus the assets it does not bundle itself.
# No node_modules install, no build toolchain.
# --------------------------------------------------------------------------
FROM node:22-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

RUN addgroup -g 10001 -S nodejs \
    && adduser -u 10001 -S nextjs -G nodejs

COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
# The standalone server serves these two only if they are copied in beside it.
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

USER nextjs

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD wget --quiet --spider http://127.0.0.1:3000/ || exit 1

CMD ["node", "server.js"]
