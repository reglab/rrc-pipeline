FROM node:20-slim AS builder

ARG BLANK_API_URL

# Install pnpm
RUN npm install -g pnpm

WORKDIR /app

# Copy lockfile and package files for better caching
COPY frontend/package.json .
COPY frontend/pnpm-lock.yaml .

# Install dependencies with frozen lockfile
RUN pnpm install --frozen-lockfile

# Copy source files
COPY frontend/ .

# Build the app
ENV VITE_BLANK_API_URL=${BLANK_API_URL}
RUN pnpm run build


# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
# Add custom nginx config
COPY --from=builder /app/nginx.conf /etc/nginx/conf.d/default.conf
