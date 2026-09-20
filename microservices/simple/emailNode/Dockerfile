# Use an official Node.js runtime as a parent image
FROM node:20-slim

# Set the working directory to /app
WORKDIR /usr/src/app/

# Copy package.json and package-lock.json to /app
COPY package*.json ./

# Install dependencies
RUN npm ci --ignore-scripts

# Copy the rest of the application code to /app
COPY src/* ./

# Start the microservice
CMD [ "node", "./notification.js" ]
