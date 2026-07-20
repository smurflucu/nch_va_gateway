FROM node:20-alpine
WORKDIR /app
# baileys pulls the `libsignal` dependency from GitHub, so git is required at install time
RUN apk add --no-cache git
COPY package.json ./
RUN npm install --omit=dev
COPY server.js ./
ENV AUTH_DIR=/app/auth
EXPOSE 3001
CMD ["node", "server.js"]
