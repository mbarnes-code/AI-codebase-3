# syntax=docker/dockerfile:1
FROM node:24-alpine AS base

# Install dependencies only when needed
FROM base AS deps
# Check https://github.com/nodejs/docker-node/tree/b4117f9333da4138b03a546ec926ef50a31506c3#nodealpine to understand why libc6-compat might be needed.
RUN apk add --no-cache libc6-compat \
    build-base \
    g++ \
    cairo \
    librsvg-dev \
    pango-dev \
    imagemagick \
    fontconfig \
    font-noto
WORKDIR /app

# Install dependencies based on the preferred package manager
COPY package.json yarn.lock* package-lock.json* pnpm-lock.yaml* ./

RUN if [ -f yarn.lock ]; then yarn --frozen-lockfile; \
    elif [ -f package-lock.json ]; then npm ci; \
    elif [ -f pnpm-lock.yaml ]; then yarn global add pnpm && pnpm i --frozen-lockfile; \
    else echo "Lockfile not found." && exit 101; \
    fi && \
    rm -f .npmrc


# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY . .
COPY --from=deps /app/node_modules ./node_modules

ARG build_type=prod
ENV BUILD_TYPE=$build_type

RUN if [ "$BUILD_TYPE" != "prod" ]; then \
    echo "NEXT_PUBLIC_CLIENT_URL=https://$BUILD_TYPE.commanderspellbook.com" >> .env.production; \
    echo "NEXT_PUBLIC_EDITOR_BACKEND_URL=https://$BUILD_TYPE-backend.commanderspellbook.com" >> .env.production; \
    fi

RUN yarn install
RUN yarn build

# If using npm comment out above and use below instead
# RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner

# Install runtime deps for canvas or other native libs
RUN apk add --no-cache \
    build-base \
    cairo \
    pango \
    librsvg \
    fontconfig \
    font-noto \
 && \
    # Ensure musl‐compatible symlinks
    ln -s /usr/lib/libcairo.so.2 /usr/lib/libcairo.so    || true && \
    ln -s /usr/lib/libpango-1.0.so.0 /usr/lib/libpango-1.0.so || true && \
    ln -s /usr/lib/libjpeg.so /usr/lib/libjpeg.so.8      || true

WORKDIR /app

ARG build_type=prod
ENV BUILD_TYPE=$build_type \
    NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

# Non-root user
RUN addgroup --system --gid 1001 nodejs \
 && adduser --system --uid 1001 nextjs

# Copy public assets
COPY --from=builder /app/public ./public

# Copy Next.js build output
COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next

# Copy node_modules
COPY --from=deps /app/node_modules ./node_modules

USER nextjs
EXPOSE 3000

CMD ["node_modules/.bin/next", "start"]