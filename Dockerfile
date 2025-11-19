FROM node:20-alpine AS base

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies with increased timeout
RUN npm install --legacy-peer-deps --network-timeout=600000 || npm install --legacy-peer-deps
RUN npm install react-is --legacy-peer-deps

# Copy source code
COPY src ./src
COPY public ./public
COPY index.html vite.config.js eslint.config.js ./

# Expose Vite dev server port
EXPOSE 5173

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:5173 || exit 1

# Run dev server with host binding for Docker
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
