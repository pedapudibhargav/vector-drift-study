ARG DOCKER_NODE_IMAGE=docker.io/library/node:22-alpine
FROM ${DOCKER_NODE_IMAGE}

WORKDIR /app

ARG NPM_REGISTRY=https://registry.npmjs.org/

COPY apps/web/package.json apps/web/package-lock.json* .npmrc* ./
RUN npm install --registry "${NPM_REGISTRY}"

COPY apps/web/ .

ENV VITE_API_PROXY_TARGET=http://vector-drift-api:8000

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
