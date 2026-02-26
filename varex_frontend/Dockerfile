# PATH: varex_frontend/Dockerfile
# Multi-stage build for Next.js frontend

FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
# Force install ALL dependencies (including devDependencies like tailwindcss)
RUN npm install --include=dev

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Ensure NODE_ENV is not set to production during build
# so Tailwind CSS and PostCSS can compile properly
ENV NODE_ENV=production
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
# Automatically leverage output traces to reduce image size
# https://nextjs.org/docs/advanced-features/output-file-tracing
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
