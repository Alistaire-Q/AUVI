FROM node:20-alpine

WORKDIR /app/frontend

# Copy package files and install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy application code
COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
