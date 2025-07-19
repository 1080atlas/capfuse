# Use Node.js 18 as base image
FROM node:18-alpine

# Install Python and ffmpeg
RUN apk add --no-cache python3 py3-pip ffmpeg

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install Node.js dependencies
RUN npm install

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p tmp/jobs output

# Build Next.js application
RUN npm run build

# Expose ports
EXPOSE 3000 3001

# Start both Next.js and Express server
CMD ["npm", "run", "dev:all"]