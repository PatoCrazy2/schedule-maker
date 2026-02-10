# frontend/Dockerfile
FROM node:22-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Exponemos el puerto de Vite
EXPOSE 5173

# Host 0.0.0.0 es necesario para que Docker exponga el puerto hacia afuera
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]