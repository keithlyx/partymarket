# Use an official Node.js runtime as a parent image
FROM node:16-slim

# Set the working directory to /app
WORKDIR /usr/src/app/

# Copy package.json and package-lock.json to /app
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code to /app
COPY src/* ./

# Start the microservice
CMD [ "node", "./notification.js" ]